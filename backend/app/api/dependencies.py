from typing import Annotated
from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User


bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    auto_error=False,
)

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    credentials: BearerCredentials,
    session: DatabaseSession,
) -> User:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
    ):
        raise authentication_error()

    subject = decode_access_token(
        credentials.credentials,
    )

    if subject is None:
        raise authentication_error()

    try:
        user_id = UUID(subject)
    except ValueError:
        raise authentication_error() from None

    user = session.get(User, user_id)

    if user is None or not user.is_active:
        raise authentication_error()

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]