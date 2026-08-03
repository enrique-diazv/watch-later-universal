from datetime import (
    datetime,
    timedelta,
    timezone,
)
from collections.abc import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import (
    decode_access_token,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db_session
from app.main import app
from app.models.email_verification_token import (
    EmailVerificationToken,
)
from app.models.refresh_token import RefreshToken
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

    EmailVerificationToken.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )

    RefreshToken.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )

    with TestSessionFactory() as session:
        session.execute(
            delete(EmailVerificationToken)
        )
        session.execute(delete(RefreshToken))
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

def mark_user_as_verified(
    email: str = "learner@example.com",
) -> None:
    with TestSessionFactory() as session:
        user = session.scalar(
            select(User).where(
                User.email == email,
            )
        )

        assert user is not None

        user.is_email_verified = True
        session.commit()


def test_register_creates_user_with_hashed_password(
    client: TestClient,
) -> None:
    password = "safe-learning-password"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Learner@EXAMPLE.COM",
            "password": password,
            "display_name": "Learner",
            "country_code": "mx",
        },
    )
    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "learner@example.com"
    assert data["country_code"] == "MX"
    assert data["is_email_verified"] is False
    assert "password" not in data
    assert "password_hash" not in data

    with TestSessionFactory() as session:
        user = session.scalar(
            select(User).where(
                User.email == "learner@example.com",
            )
        )
        verification_token = session.scalar(
            select(EmailVerificationToken)
        )

    assert user is not None
    assert verification_token is not None
    assert len(verification_token.token_hash) == 64
    assert verification_token.used_at is None
    assert user.password_hash != password
    assert verify_password(
        password,
        user.password_hash,
    )


def test_register_rejects_duplicate_email(
    client: TestClient,
) -> None:
    payload = {
        "email": "learner@example.com",
        "password": "safe-learning-password",
        "display_name": "Learner",
        "country_code": "MX",
    }

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    payload["email"] = "  LEARNER@example.com "

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "El correo ya está registrado.",
    }

def test_email_verification_allows_login(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_tokens: list[str] = []

    def capture_verification_email(
        recipient_email: str,
        display_name: str,
        raw_token: str,
    ) -> None:
        assert recipient_email == (
            "learner@example.com"
        )
        assert display_name == "Learner"
        sent_tokens.append(raw_token)

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth."
        "send_verification_email",
        capture_verification_email,
    )

    registration_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    assert registration_response.status_code == 201
    assert len(sent_tokens) == 1

    blocked_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    assert blocked_login_response.status_code == 403
    assert blocked_login_response.json() == {
        "detail": (
            "Debes confirmar tu correo antes "
            "de iniciar sesión."
        ),
    }

    verification_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": sent_tokens[0],
        },
    )

    assert verification_response.status_code == 200
    assert verification_response.json() == {
        "message": (
            "Tu correo fue verificado correctamente."
        ),
    }

    repeated_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": sent_tokens[0],
        },
    )

    assert repeated_response.status_code == 400

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    assert login_response.status_code == 200

    with TestSessionFactory() as session:
        user = session.scalar(
            select(User).where(
                User.email == "learner@example.com",
            )
        )
        stored_token = session.scalar(
            select(EmailVerificationToken)
        )

    assert user is not None
    assert user.is_email_verified is True
    assert stored_token is not None
    assert stored_token.used_at is not None

def test_resend_verification_respects_cooldown(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_tokens: list[str] = []

    def capture_verification_email(
        recipient_email: str,
        display_name: str,
        raw_token: str,
    ) -> None:
        sent_tokens.append(raw_token)

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth."
        "send_verification_email",
        capture_verification_email,
    )

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    assert len(sent_tokens) == 1

    immediate_response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "learner@example.com",
        },
    )

    assert immediate_response.status_code == 202
    assert len(sent_tokens) == 1

    with TestSessionFactory() as session:
        stored_token = session.scalar(
            select(EmailVerificationToken)
        )

        assert stored_token is not None

        stored_token.created_at = (
            datetime.now(timezone.utc)
            - timedelta(seconds=61)
        )
        session.commit()

    resend_response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "learner@example.com",
        },
    )

    assert resend_response.status_code == 202
    assert len(sent_tokens) == 2
    assert sent_tokens[1] != sent_tokens[0]

    old_token_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": sent_tokens[0],
        },
    )

    assert old_token_response.status_code == 400

    new_token_response = client.post(
        "/api/v1/auth/verify-email",
        json={
            "token": sent_tokens[1],
        },
    )

    assert new_token_response.status_code == 200

def test_login_returns_valid_access_token(
    client: TestClient,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    user_id = registration_response.json()["id"]

    mark_user_as_verified()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "LEARNER@example.com",
            "password": "safe-learning-password",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800
    assert (
        decode_access_token(data["access_token"])
        == user_id
    )

def test_login_rejects_wrong_password(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Correo o contraseña incorrectos.",
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_login_rejects_unknown_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "safe-learning-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Correo o contraseña incorrectos.",
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )

def test_me_returns_authenticated_user(
    client: TestClient,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    registered_user = registration_response.json()

    mark_user_as_verified()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    access_token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registered_user["id"]
    assert data["email"] == "learner@example.com"
    assert data["display_name"] == "Learner"
    assert "password" not in data
    assert "password_hash" not in data

def test_me_rejects_missing_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": (
            "No se pudieron validar las credenciales."
        ),
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_me_rejects_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": (
            "No se pudieron validar las credenciales."
        ),
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )

def test_login_sets_hashed_refresh_token_cookie(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    mark_user_as_verified()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    assert response.status_code == 200

    raw_refresh_token = response.cookies.get(
        "refresh_token"
    )

    assert raw_refresh_token is not None
    assert "HttpOnly" in response.headers["set-cookie"]
    assert (
        "Path=/api/v1/auth"
        in response.headers["set-cookie"]
    )

    with TestSessionFactory() as session:
        stored_token = session.scalar(
            select(RefreshToken)
        )

    assert stored_token is not None
    assert stored_token.token_hash != raw_refresh_token
    assert stored_token.token_hash == (
        hash_refresh_token(raw_refresh_token)
    )

def test_refresh_rotates_token_and_returns_access_token(
    client: TestClient,
) -> None:
    registration_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )

    user_id = registration_response.json()["id"]

    mark_user_as_verified()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    old_refresh_token = login_response.cookies.get(
        "refresh_token"
    )

    assert old_refresh_token is not None

    refresh_response = client.post(
        "/api/v1/auth/refresh",
    )

    assert refresh_response.status_code == 200

    new_refresh_token = refresh_response.cookies.get(
        "refresh_token"
    )
    data = refresh_response.json()

    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token
    assert (
        decode_access_token(data["access_token"])
        == user_id
    )

    with TestSessionFactory() as session:
        stored_tokens = list(
            session.scalars(
                select(RefreshToken)
            ).all()
        )

    assert len(stored_tokens) == 2

    old_stored_token = next(
        token
        for token in stored_tokens
        if token.token_hash
        == hash_refresh_token(old_refresh_token)
    )
    new_stored_token = next(
        token
        for token in stored_tokens
        if token.token_hash
        == hash_refresh_token(new_refresh_token)
    )

    assert old_stored_token.revoked_at is not None
    assert new_stored_token.revoked_at is None
    assert (
        old_stored_token.family_id
        == new_stored_token.family_id
    )

def test_refresh_rejects_missing_cookie(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/refresh",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": (
            "No se pudieron validar las credenciales."
        ),
    }


def test_refresh_reuse_revokes_token_family(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )
    mark_user_as_verified()
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    old_refresh_token = login_response.cookies.get(
        "refresh_token"
    )

    assert old_refresh_token is not None

    first_refresh_response = client.post(
        "/api/v1/auth/refresh",
    )

    assert first_refresh_response.status_code == 200

    client.cookies.clear()
    client.cookies.set(
        "refresh_token",
        old_refresh_token,
        path="/api/v1/auth",
    )

    reuse_response = client.post(
        "/api/v1/auth/refresh",
    )

    assert reuse_response.status_code == 401

    with TestSessionFactory() as session:
        active_tokens = list(
            session.scalars(
                select(RefreshToken).where(
                    RefreshToken.revoked_at.is_(None),
                )
            ).all()
        )

    assert active_tokens == []

def test_logout_revokes_session_and_clears_cookie(
    client: TestClient,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
            "display_name": "Learner",
            "country_code": "MX",
        },
    )
    mark_user_as_verified()
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "learner@example.com",
            "password": "safe-learning-password",
        },
    )

    logout_response = client.post(
        "/api/v1/auth/logout",
    )

    assert logout_response.status_code == 204
    assert logout_response.content == b""
    assert (
        client.cookies.get("refresh_token")
        is None
    )

    with TestSessionFactory() as session:
        stored_token = session.scalar(
            select(RefreshToken)
        )

    assert stored_token is not None
    assert stored_token.revoked_at is not None

    refresh_response = client.post(
        "/api/v1/auth/refresh",
    )

    assert refresh_response.status_code == 401

def test_logout_without_cookie_is_idempotent(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/logout",
    )

    assert response.status_code == 204
    assert response.content == b""