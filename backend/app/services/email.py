import logging
from html import escape
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


def build_email_verification_url(
    raw_token: str,
) -> str:
    settings = get_settings()
    query = urlencode({
        "token": raw_token,
    })

    return (
        f"{settings.frontend_base_url.rstrip('/')}"
        f"/verify-email?{query}"
    )


def send_verification_email(
    recipient_email: str,
    display_name: str,
    raw_token: str,
) -> None:
    settings = get_settings()
    verification_url = (
        build_email_verification_url(raw_token)
    )

    if settings.email_delivery_mode == "console":
        logger.warning(
            "Enlace de verificación para %s: %s",
            recipient_email,
            verification_url,
        )
        return

    if settings.brevo_api_key is None:
        raise EmailDeliveryError(
            "BREVO_API_KEY no está configurada.",
        )

    safe_name = escape(display_name)
    safe_url = escape(
        verification_url,
        quote=True,
    )

    payload = {
        "sender": {
            "email": settings.email_from_address,
            "name": settings.email_from_name,
        },
        "to": [
            {
                "email": recipient_email,
                "name": display_name,
            },
        ],
        "subject": (
            "Confirma tu correo en Watch Later Universal"
        ),
        "textContent": (
            f"Hola {display_name},\n\n"
            "Confirma tu correo abriendo este enlace:\n"
            f"{verification_url}\n\n"
            "Este enlace expirará pronto. "
            "Si no creaste esta cuenta, "
            "puedes ignorar este mensaje."
        ),
        "htmlContent": (
            "<h1>Confirma tu correo</h1>"
            f"<p>Hola {safe_name},</p>"
            "<p>Confirma tu cuenta de "
            "Watch Later Universal:</p>"
            f'<p><a href="{safe_url}">'
            "Confirmar mi correo"
            "</a></p>"
            "<p>Si no creaste esta cuenta, "
            "puedes ignorar este mensaje.</p>"
        ),
    }

    headers = {
        "accept": "application/json",
        "api-key": (
            settings
            .brevo_api_key
            .get_secret_value()
        ),
        "content-type": "application/json",
    }

    try:
        response = httpx.post(
            settings.brevo_api_url,
            headers=headers,
            json=payload,
            timeout=(
                settings.email_request_timeout_seconds
            ),
        )
    except httpx.HTTPError as error:
        raise EmailDeliveryError(
            "No fue posible contactar a Brevo.",
        ) from error

    if response.is_error:
        raise EmailDeliveryError(
            "Brevo rechazó el correo "
            f"con código {response.status_code}.",
        )