from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
    )

    country_code: Mapped[str] = mapped_column(
        String(2),
        default="MX",
        server_default="MX",
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
    )

    is_email_verified: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
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