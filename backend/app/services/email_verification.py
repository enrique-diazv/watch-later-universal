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
    create_email_verification_token,
    hash_email_verification_token,
)
from app.models.email_verification_token import (
    EmailVerificationToken,
)
from app.models.user import User


def issue_email_verification_token(
    session: Session,
    user_id: UUID,
) -> tuple[str, EmailVerificationToken]:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    session.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_token = create_email_verification_token()

    stored_token = EmailVerificationToken(
        user_id=user_id,
        token_hash=hash_email_verification_token(
            raw_token,
        ),
        expires_at=(
            now
            + timedelta(
                hours=(
                    settings
                    .email_verification_token_expire_hours
                ),
            )
        ),
    )

    session.add(stored_token)

    return raw_token, stored_token


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)

def can_resend_email_verification(
    session: Session,
    user_id: UUID,
) -> bool:
    latest_created_at = session.scalar(
        select(EmailVerificationToken.created_at)
        .where(
            EmailVerificationToken.user_id == user_id,
        )
        .order_by(
            EmailVerificationToken.created_at.desc(),
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
                .email_verification_resend_cooldown_seconds
            ),
        )
    )

    return datetime.now(timezone.utc) >= next_allowed_at

def consume_email_verification_token(
    session: Session,
    raw_token: str,
) -> User | None:
    stored_token = session.scalar(
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.token_hash
            == hash_email_verification_token(
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

    if user is None or not user.is_active:
        stored_token.used_at = now
        return None

    stored_token.used_at = now
    user.is_email_verified = True

    session.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.id
            != stored_token.id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    return user