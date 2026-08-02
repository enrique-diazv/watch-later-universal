from collections.abc import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.main import app
from app.models.library import LibraryItem, LibraryStatus
from app.models.media import Media, MediaType
from app.models.user import User


test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionFactory = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db_session(
) -> Generator[Session, None, None]:
    with TestSessionFactory() as session:
        yield session


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv(
        "TMDB_ACCESS_TOKEN",
        "test-tmdb-token",
    )
    monkeypatch.setenv(
        "DATABASE_PASSWORD",
        "test-database-password",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-only-for-automated-tests",
    )

    get_settings.cache_clear()

    User.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )
    Media.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )
    LibraryItem.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )

    with TestSessionFactory() as session:
        session.execute(delete(LibraryItem))
        session.execute(delete(Media))
        session.execute(delete(User))
        session.commit()

    app.dependency_overrides[get_db_session] = (
        override_get_db_session
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(
        get_db_session,
        None,
    )

    get_settings.cache_clear()


def test_create_library_item_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/library",
        json={
            "tmdb_id": 550,
            "media_type": "movie",
            "status": "plan_to_watch",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": (
            "No se pudieron validar las credenciales."
        ),
    }

def test_create_library_item_persists_tmdb_media(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestSessionFactory() as session:
        user = User(
            email="learner@example.com",
            password_hash="not-used-in-this-test",
            display_name="Learner",
            country_code="MX",
        )
        session.add(user)
        session.commit()

        user_id = user.id

    access_token = create_access_token(
        str(user_id),
    )

    async def fake_get_media_details(
        media_type: str,
        tmdb_id: int,
    ) -> dict[str, object]:
        assert media_type == "movie"
        assert tmdb_id == 550

        return {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "An insomniac meets Tyler.",
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "vote_count": 30000,
            "runtime": 139,
        }

    monkeypatch.setattr(
        (
            "app.api.v1.endpoints.library."
            "get_media_details"
        ),
        fake_get_media_details,
    )

    response = client.post(
        "/api/v1/library",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        json={
            "tmdb_id": 550,
            "media_type": "movie",
            "status": "plan_to_watch",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "plan_to_watch"
    assert data["media"]["tmdb_id"] == 550
    assert data["media"]["media_type"] == "movie"
    assert data["media"]["title"] == "Fight Club"
    assert data["media"]["poster_path"] == (
        "/poster.jpg"
    )

    with TestSessionFactory() as session:
        stored_item = session.scalar(
            select(LibraryItem)
        )
        stored_media = session.scalar(
            select(Media)
        )

    assert stored_item is not None
    assert stored_media is not None
    assert stored_item.user_id == user_id
    assert stored_item.media_id == stored_media.id

def test_create_library_item_rejects_duplicate(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestSessionFactory() as session:
        user = User(
            email="learner@example.com",
            password_hash="not-used-in-this-test",
            display_name="Learner",
            country_code="MX",
        )
        session.add(user)
        session.commit()

        access_token = create_access_token(
            str(user.id),
        )

    tmdb_calls = 0

    async def fake_get_media_details(
        media_type: str,
        tmdb_id: int,
    ) -> dict[str, object]:
        nonlocal tmdb_calls

        tmdb_calls += 1

        return {
            "id": tmdb_id,
            "title": "Fight Club",
            "release_date": "1999-10-15",
        }

    monkeypatch.setattr(
        (
            "app.api.v1.endpoints.library."
            "get_media_details"
        ),
        fake_get_media_details,
    )

    payload = {
        "tmdb_id": 550,
        "media_type": "movie",
        "status": "plan_to_watch",
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    first_response = client.post(
        "/api/v1/library",
        headers=headers,
        json=payload,
    )
    duplicate_response = client.post(
        "/api/v1/library",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": (
            "El contenido ya está en tu biblioteca."
        ),
    }
    assert tmdb_calls == 1

    with TestSessionFactory() as session:
        stored_items = list(
            session.scalars(
                select(LibraryItem)
            ).all()
        )

    assert len(stored_items) == 1

def test_list_library_returns_only_current_user_items(
    client: TestClient,
) -> None:
    with TestSessionFactory() as session:
        first_user = User(
            email="first@example.com",
            password_hash="not-used",
            display_name="First",
            country_code="MX",
        )
        second_user = User(
            email="second@example.com",
            password_hash="not-used",
            display_name="Second",
            country_code="MX",
        )
        first_media = Media(
            tmdb_id=550,
            media_type=MediaType.MOVIE,
            title="Fight Club",
        )
        second_media = Media(
            tmdb_id=1399,
            media_type=MediaType.TV,
            title="Game of Thrones",
        )

        session.add_all(
            [
                first_user,
                second_user,
                first_media,
                second_media,
            ]
        )
        session.flush()

        session.add_all(
            [
                LibraryItem(
                    user_id=first_user.id,
                    media=first_media,
                ),
                LibraryItem(
                    user_id=second_user.id,
                    media=second_media,
                ),
            ]
        )
        session.commit()

        access_token = create_access_token(
            str(first_user.id),
        )

    response = client.get(
        "/api/v1/library",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["media"]["tmdb_id"] == 550
    assert data[0]["media"]["title"] == "Fight Club"

def test_update_library_item_changes_user_fields(
    client: TestClient,
) -> None:
    with TestSessionFactory() as session:
        user = User(
            email="learner@example.com",
            password_hash="not-used",
            display_name="Learner",
            country_code="MX",
        )
        media = Media(
            tmdb_id=550,
            media_type=MediaType.MOVIE,
            title="Fight Club",
        )

        session.add_all([user, media])
        session.flush()

        library_item = LibraryItem(
            user_id=user.id,
            media=media,
        )
        session.add(library_item)
        session.commit()

        item_id = library_item.id
        access_token = create_access_token(
            str(user.id),
        )

    response = client.patch(
        f"/api/v1/library/{item_id}",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
        json={
            "status": "completed",
            "user_rating": 9.5,
            "is_favorite": True,
            "notes": "Una película memorable.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["user_rating"] == 9.5
    assert data["is_favorite"] is True
    assert data["notes"] == (
        "Una película memorable."
    )
    assert data["started_at"] is not None
    assert data["completed_at"] is not None

    with TestSessionFactory() as session:
        stored_item = session.get(
            LibraryItem,
            item_id,
        )

    assert stored_item is not None
    assert (
        stored_item.status
        == LibraryStatus.COMPLETED
    )
    assert stored_item.user_rating == 9.5
    assert stored_item.is_favorite is True

def test_update_library_item_rejects_other_user(
    client: TestClient,
) -> None:
    with TestSessionFactory() as session:
        owner = User(
            email="owner@example.com",
            password_hash="not-used",
            display_name="Owner",
            country_code="MX",
        )
        other_user = User(
            email="other@example.com",
            password_hash="not-used",
            display_name="Other",
            country_code="MX",
        )
        media = Media(
            tmdb_id=550,
            media_type=MediaType.MOVIE,
            title="Fight Club",
        )

        session.add_all(
            [owner, other_user, media]
        )
        session.flush()

        library_item = LibraryItem(
            user_id=owner.id,
            media=media,
        )
        session.add(library_item)
        session.commit()

        item_id = library_item.id
        other_user_token = create_access_token(
            str(other_user.id),
        )

    response = client.patch(
        f"/api/v1/library/{item_id}",
        headers={
            "Authorization": (
                f"Bearer {other_user_token}"
            ),
        },
        json={
            "status": "completed",
            "user_rating": 10,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Elemento no encontrado "
            "en tu biblioteca."
        ),
    }

    with TestSessionFactory() as session:
        stored_item = session.get(
            LibraryItem,
            item_id,
        )

    assert stored_item is not None
    assert (
        stored_item.status
        == LibraryStatus.PLAN_TO_WATCH
    )
    assert stored_item.user_rating is None

def test_delete_library_item_keeps_media_catalog(
    client: TestClient,
) -> None:
    with TestSessionFactory() as session:
        user = User(
            email="learner@example.com",
            password_hash="not-used",
            display_name="Learner",
            country_code="MX",
        )
        media = Media(
            tmdb_id=550,
            media_type=MediaType.MOVIE,
            title="Fight Club",
        )

        session.add_all([user, media])
        session.flush()

        library_item = LibraryItem(
            user_id=user.id,
            media=media,
        )
        session.add(library_item)
        session.commit()

        item_id = library_item.id
        media_id = media.id
        access_token = create_access_token(
            str(user.id),
        )

    response = client.delete(
        f"/api/v1/library/{item_id}",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
    )

    assert response.status_code == 204
    assert response.content == b""

    with TestSessionFactory() as session:
        deleted_item = session.get(
            LibraryItem,
            item_id,
        )
        stored_media = session.get(
            Media,
            media_id,
        )

    assert deleted_item is None
    assert stored_media is not None

def test_delete_library_item_rejects_other_user(
    client: TestClient,
) -> None:
    with TestSessionFactory() as session:
        owner = User(
            email="owner@example.com",
            password_hash="not-used",
            display_name="Owner",
            country_code="MX",
        )
        other_user = User(
            email="other@example.com",
            password_hash="not-used",
            display_name="Other",
            country_code="MX",
        )
        media = Media(
            tmdb_id=550,
            media_type=MediaType.MOVIE,
            title="Fight Club",
        )

        session.add_all(
            [owner, other_user, media]
        )
        session.flush()

        library_item = LibraryItem(
            user_id=owner.id,
            media=media,
        )
        session.add(library_item)
        session.commit()

        item_id = library_item.id
        other_user_token = create_access_token(
            str(other_user.id),
        )

    response = client.delete(
        f"/api/v1/library/{item_id}",
        headers={
            "Authorization": (
                f"Bearer {other_user_token}"
            ),
        },
    )

    assert response.status_code == 404

    with TestSessionFactory() as session:
        stored_item = session.get(
            LibraryItem,
            item_id,
        )

    assert stored_item is not None