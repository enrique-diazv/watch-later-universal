from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.dependencies import (
    CurrentUser,
    authentication_error,
)
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
from app.services.auth import (
    issue_refresh_token,
    revoke_refresh_token_family,
    rotate_refresh_token,
)

router = APIRouter()

DatabaseSession = Annotated[
    Session,
    Depends(get_db_session),
]

def set_refresh_cookie(
    response: Response,
    token: str,
) -> None:
    settings = get_settings()

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=(
            settings.refresh_token_expire_days
            * 24
            * 60
            * 60
        ),
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        path="/api/v1/auth",
    )

def clear_refresh_cookie(
    response: Response,
) -> None:
    settings = get_settings()

    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/v1/auth",
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="lax",
    )

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
    response: Response,
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

    refresh_token, _ = issue_refresh_token(
        session,
        user.id,
    )

    session.commit()

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=(
            settings.access_token_expire_minutes * 60
        ),
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_session(
    request: Request,
    response: Response,
    session: DatabaseSession,
) -> TokenResponse:
    settings = get_settings()

    raw_refresh_token = request.cookies.get(
        settings.refresh_cookie_name,
    )

    if raw_refresh_token is None:
        raise authentication_error()

    rotation = rotate_refresh_token(
        session,
        raw_refresh_token,
    )

    if rotation is None:
        session.commit()
        raise authentication_error()

    new_refresh_token, user = rotation

    session.commit()

    set_refresh_cookie(
        response,
        new_refresh_token,
    )

    access_token = create_access_token(
        str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=(
            settings.access_token_expire_minutes * 60
        ),
    )

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_session(
    request: Request,
    response: Response,
    session: DatabaseSession,
) -> None:
    settings = get_settings()

    raw_refresh_token = request.cookies.get(
        settings.refresh_cookie_name,
    )

    if raw_refresh_token is not None:
        revoke_refresh_token_family(
            session,
            raw_refresh_token,
        )
        session.commit()

    clear_refresh_cookie(response)

@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: CurrentUser,
) -> User:
    return current_user