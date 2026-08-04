from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import (
    Engine,
    URL,
    make_url,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_database_url() -> URL:
    settings = get_settings()

    if settings.database_url is not None:
        raw_database_url = (
            settings
            .database_url
            .get_secret_value()
            .strip()
        )

        if raw_database_url:
            database_url = make_url(raw_database_url)

            if database_url.drivername in {
                "postgres",
                "postgresql",
            }:
                database_url = database_url.set(
                    drivername="postgresql+psycopg",
                )

            return database_url

    if settings.database_password is None:
        raise RuntimeError(
            "Configura DATABASE_URL o "
            "DATABASE_PASSWORD.",
        )

    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.database_user,
        password=(
            settings
            .database_password
            .get_secret_value()
        ),
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
    )


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        build_database_url(),
        pool_pre_ping=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        expire_on_commit=False,
    )


def get_db_session() -> Generator[Session, None, None]:
    session_factory = get_session_factory()

    with session_factory() as session:
        yield session