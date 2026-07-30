from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SqlEnum,
    Float,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MediaType(str, Enum):
    MOVIE = "movie"
    TV = "tv"


class Media(Base):
    __tablename__ = "media"
    __table_args__ = (
        UniqueConstraint(
            "tmdb_id",
            "media_type",
            name="uq_media_tmdb_id_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    tmdb_id: Mapped[int]
    media_type: Mapped[MediaType] = mapped_column(
        SqlEnum(
            MediaType,
            name="media_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
    )
    title: Mapped[str] = mapped_column(String(255))
    original_title: Mapped[str | None] = mapped_column(
        String(255),
    )
    overview: Mapped[str | None] = mapped_column(Text)
    poster_path: Mapped[str | None] = mapped_column(
        String(255),
    )
    backdrop_path: Mapped[str | None] = mapped_column(
        String(255),
    )
    release_date: Mapped[date | None] = mapped_column(Date)
    tmdb_rating: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0",
    )
    vote_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
    )
    runtime: Mapped[int | None]
    metadata_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )