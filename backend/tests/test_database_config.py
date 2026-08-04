import pytest

from app.core.config import get_settings
from app.db.session import build_database_url


def test_neon_database_url_uses_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TMDB_ACCESS_TOKEN",
        "test-tmdb-token",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-jwt-secret",
    )
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://test-user:test-password"
            "@ep-example-pooler.neon.tech/watch_later"
            "?sslmode=require"
        ),
    )

    get_settings.cache_clear()

    try:
        database_url = build_database_url()

        assert database_url.drivername == (
            "postgresql+psycopg"
        )
        assert database_url.host == (
            "ep-example-pooler.neon.tech"
        )
        assert database_url.database == "watch_later"
        assert database_url.query["sslmode"] == "require"
    finally:
        get_settings.cache_clear()