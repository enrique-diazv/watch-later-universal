from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LibraryStatus(str, Enum):
    PLAN_TO_WATCH = "plan_to_watch"
    WATCHING = "watching"
    COMPLETED = "completed"
    PAUSED = "paused"
    DROPPED = "dropped"


class LibraryItem(Base):
    __tablename__ = "user_library"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "media_id",
            name="uq_user_library_user_media",
        ),
        CheckConstraint(
            "user_rating IS NULL OR "
            "(user_rating >= 0 AND user_rating <= 10)",
            name="ck_user_library_rating_range",
        ),
        Index(
            "ix_user_library_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_user_library_user_updated_at",
            "user_id",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"),
    )
    status: Mapped[LibraryStatus] = mapped_column(
        SqlEnum(
            LibraryStatus,
            name="library_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        default=LibraryStatus.PLAN_TO_WATCH,
        server_default="PLAN_TO_WATCH",
    )
    user_rating: Mapped[float | None] = mapped_column(Float)
    is_favorite: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )