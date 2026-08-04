from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_password_reset_token,
    hash_password,
    hash_password_reset_token,
)
from app.models.password_reset_token import (
    PasswordResetToken,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User

def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def issue_password_reset_token(
    session: Session,
    user_id: UUID,
) -> tuple[str, PasswordResetToken]:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_token = create_password_reset_token()

    stored_token = PasswordResetToken(
        user_id=user_id,
        token_hash=hash_password_reset_token(
            raw_token,
        ),
        expires_at=(
            now
            + timedelta(
                minutes=(
                    settings
                    .password_reset_token_expire_minutes
                ),
            )
        ),
    )

    session.add(stored_token)

    return raw_token, stored_token


def can_request_password_reset(
    session: Session,
    user_id: UUID,
) -> bool:
    latest_created_at = session.scalar(
        select(PasswordResetToken.created_at)
        .where(
            PasswordResetToken.user_id == user_id,
        )
        .order_by(
            PasswordResetToken.created_at.desc(),
        )
        .limit(1)
    )

    if latest_created_at is None:
        return True

    settings = get_settings()
    next_allowed_at = (
        _as_utc(latest_created_at)
        + timedelta(
            seconds=(
                settings
                .password_reset_request_cooldown_seconds
            ),
        )
    )

    return datetime.now(timezone.utc) >= next_allowed_at

def consume_password_reset_token(
    session: Session,
    raw_token: str,
    new_password: str,
) -> User | None:
    stored_token = session.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash
            == hash_password_reset_token(
                raw_token,
            )
        )
        .with_for_update()
    )

    if stored_token is None:
        return None

    now = datetime.now(timezone.utc)

    if stored_token.used_at is not None:
        return None

    if _as_utc(stored_token.expires_at) <= now:
        stored_token.used_at = now
        return None

    user = session.get(
        User,
        stored_token.user_id,
    )

    if (
        user is None
        or not user.is_active
        or not user.is_email_verified
    ):
        stored_token.used_at = now
        return None

    stored_token.used_at = now
    user.password_hash = hash_password(new_password)

    session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != stored_token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    return user