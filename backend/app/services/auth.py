from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_refresh_token,
    hash_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User

def issue_refresh_token(
    session: Session,
    user_id: UUID,
    family_id: UUID | None = None,
) -> tuple[str, RefreshToken]:
    settings = get_settings()

    raw_token = create_refresh_token()

    refresh_token = RefreshToken(
        user_id=user_id,
        family_id=family_id or uuid4(),
        token_hash=hash_refresh_token(raw_token),
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                days=settings.refresh_token_expire_days,
            )
        ),
    )

    session.add(refresh_token)

    return raw_token, refresh_token

def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def rotate_refresh_token(
    session: Session,
    raw_token: str,
) -> tuple[str, User] | None:
    stored_token = session.scalar(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash
            == hash_refresh_token(raw_token),
        )
        .with_for_update()
    )

    if stored_token is None:
        return None

    now = datetime.now(timezone.utc)

    if stored_token.revoked_at is not None:
        session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id
                == stored_token.family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        return None

    if as_utc(stored_token.expires_at) <= now:
        stored_token.revoked_at = now
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
        stored_token.revoked_at = now
        return None

    stored_token.revoked_at = now

    new_raw_token, _ = issue_refresh_token(
        session,
        user.id,
        family_id=stored_token.family_id,
    )

    return new_raw_token, user

def revoke_refresh_token_family(
    session: Session,
    raw_token: str,
) -> bool:
    stored_token = session.scalar(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash
            == hash_refresh_token(raw_token),
        )
        .with_for_update()
    )

    if stored_token is None:
        return False

    session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id
            == stored_token.family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(
            revoked_at=datetime.now(timezone.utc),
        )
    )

    return True