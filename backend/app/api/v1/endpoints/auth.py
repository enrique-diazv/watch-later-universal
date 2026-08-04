import logging
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
    EmailVerificationConfirm,
    EmailVerificationResend,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
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

from app.services.email import (
    EmailDeliveryError,
    send_password_reset_email,
    send_verification_email,
)
from app.services.email_verification import (
    can_resend_email_verification,
    consume_email_verification_token,
    issue_email_verification_token,
)

from app.services.password_reset import (
    can_request_password_reset,
    consume_password_reset_token,
    issue_password_reset_token,
)

logger = logging.getLogger(__name__)
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
        max_age=(settings.refresh_token_expire_days * 24 * 60 * 60),
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
        is_email_verified=False,
    )

    session.add(user)

    try:
        session.flush()

        raw_token, _ = issue_email_verification_token(
            session,
            user.id,
        )

        session.commit()
    except IntegrityError as error:
        session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado.",
        ) from error

    session.refresh(user)

    try:
        send_verification_email(
            user.email,
            user.display_name,
            raw_token,
        )
    except EmailDeliveryError as error:
        raise HTTPException(
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            detail=(
                "La cuenta fue creada, pero no fue "
                "posible enviar la confirmación. "
                "Solicita un nuevo correo."
            ),
        ) from error

    return user


@router.post(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    payload: EmailVerificationConfirm,
    session: DatabaseSession,
) -> MessageResponse:
    user = consume_email_verification_token(
        session,
        payload.token,
    )

    if user is None:
        session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("El enlace de verificación no es " "válido o ya expiró."),
        )

    session.commit()

    return MessageResponse(
        message="Tu correo fue verificado correctamente.",
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def resend_verification_email(
    payload: EmailVerificationResend,
    session: DatabaseSession,
) -> MessageResponse:
    generic_message = (
        "Si existe una cuenta pendiente con ese correo, "
        "enviaremos un nuevo enlace de verificación."
    )

    user = session.scalar(
        select(User).where(
            User.email == str(payload.email),
        )
    )

    if user is None or not user.is_active or user.is_email_verified:
        return MessageResponse(
            message=generic_message,
        )

    if not can_resend_email_verification(
        session,
        user.id,
    ):
        return MessageResponse(
            message=generic_message,
        )

    raw_token, _ = issue_email_verification_token(
        session,
        user.id,
    )
    session.commit()

    try:
        send_verification_email(
            user.email,
            user.display_name,
            raw_token,
        )
    except EmailDeliveryError as error:
        raise HTTPException(
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            detail=(
                "No fue posible enviar el correo "
                "de verificación. Inténtalo más tarde."
            ),
        ) from error
    return MessageResponse(
        message=generic_message,
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    payload: PasswordResetRequest,
    session: DatabaseSession,
) -> MessageResponse:
    generic_message = (
        "Si existe una cuenta verificada con ese correo, "
        "enviaremos instrucciones para restablecer "
        "la contraseña."
    )

    user = session.scalar(
        select(User).where(
            User.email == str(payload.email),
        )
    )

    if (
        user is None
        or not user.is_active
        or not user.is_email_verified
    ):
        return MessageResponse(
            message=generic_message,
        )

    if not can_request_password_reset(
        session,
        user.id,
    ):
        return MessageResponse(
            message=generic_message,
        )

    raw_token, _ = issue_password_reset_token(
        session,
        user.id,
    )
    session.commit()

    try:
        send_password_reset_email(
            user.email,
            user.display_name,
            raw_token,
        )
    except EmailDeliveryError:
        logger.exception(
            "No fue posible enviar el correo "
            "de recuperación.",
        )

    return MessageResponse(
        message=generic_message,
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    payload: PasswordResetConfirm,
    session: DatabaseSession,
    response: Response,
) -> MessageResponse:
    user = consume_password_reset_token(
        session,
        payload.token,
        payload.new_password,
    )

    if user is None:
        session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El enlace de recuperación no es "
                "válido o ya expiró."
            ),
        )

    session.commit()
    clear_refresh_cookie(response)

    return MessageResponse(
        message=(
            "Tu contraseña fue actualizada "
            "correctamente."
        ),
    )

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

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=("Debes confirmar tu correo antes " "de iniciar sesión."),
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
        expires_in=(settings.access_token_expire_minutes * 60),
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
        expires_in=(settings.access_token_expire_minutes * 60),
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
