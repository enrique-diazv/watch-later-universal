from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)


from app.db.session import get_db_session
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRead,
)

router = APIRouter()

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserCreate,
    session: DatabaseSession,
) -> User:
    existing_user = session.scalar(
        select(User).where(
            User.email == str(payload.email),
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado.",
        )

    user = User(
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        country_code=payload.country_code,
    )

    session.add(user)

    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado.",
        ) from error

    session.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    payload: UserLogin,
    session: DatabaseSession,
) -> TokenResponse:
    user = session.scalar(
        select(User).where(
            User.email == str(payload.email),
        )
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    settings = get_settings()

    access_token = create_access_token(
        str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=(
            settings.access_token_expire_minutes * 60
        ),
    )