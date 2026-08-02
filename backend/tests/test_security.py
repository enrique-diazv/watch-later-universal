from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    create_refresh_token,
    hash_refresh_token,
)


TEST_JWT_SECRET = "test-secret-only-for-automated-tests"


@pytest.fixture
def configured_jwt_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
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
        TEST_JWT_SECRET,
    )

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


def test_hash_password_uses_argon2_and_random_salt() -> None:
    password = "learning-only-password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash.startswith("$argon2")
    assert second_hash.startswith("$argon2")
    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password(
        "learning-only-password",
    )

    assert (
        verify_password(
            "wrong-password",
            password_hash,
        )
        is False
    )


def test_access_token_round_trip(
    configured_jwt_settings: None,
) -> None:
    token = create_access_token("user-123")

    assert len(token.split(".")) == 3
    assert decode_access_token(token) == "user-123"


def test_access_token_rejects_malformed_token(
    configured_jwt_settings: None,
) -> None:
    assert decode_access_token("invalid-token") is None


def test_access_token_rejects_expired_token(
    configured_jwt_settings: None,
) -> None:
    expired_token = jwt.encode(
        {
            "sub": "user-123",
            "type": "access",
            "exp": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ),
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )

    assert decode_access_token(expired_token) is None

def test_refresh_tokens_are_random_and_hashed() -> None:
    first_token = create_refresh_token()
    second_token = create_refresh_token()

    first_hash = hash_refresh_token(first_token)

    assert first_token != second_token
    assert len(first_token) >= 64
    assert len(first_hash) == 64
    assert first_hash != first_token
    assert (
        hash_refresh_token(first_token)
        == first_hash
    )