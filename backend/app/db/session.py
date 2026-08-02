from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from app.core.config import get_settings

from collections.abc import Generator
from sqlalchemy.orm import Session, sessionmaker

@lru_cache
def get_engine() -> Engine:
    settings = get_settings()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.database_user,
        password=settings.database_password.get_secret_value(),
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
    )

    return create_engine(
        database_url,
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