from collections.abc import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import verify_password
from app.db.session import get_db_session
from app.main import app
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
def client() -> Iterator[TestClient]:
    User.__table__.create(
        bind=test_engine,
        checkfirst=True,
    )

    with TestSessionFactory() as session:
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
    assert "password" not in data
    assert "password_hash" not in data

    with TestSessionFactory() as session:
        user = session.scalar(
            select(User).where(
                User.email == "learner@example.com",
            )
        )

    assert user is not None
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