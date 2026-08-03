from collections.abc import Iterator

import httpx
import pytest

from app.core.config import get_settings
from app.services.email import (
    EmailDeliveryError,
    build_email_verification_url,
    send_verification_email,
)


@pytest.fixture
def configured_email_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    monkeypatch.setenv(
        "TMDB_ACCESS_TOKEN",
        "test-tmdb-token",
    )
    monkeypatch.setenv(
        "DATABASE_PASSWORD",
        "test-database-password",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-jwt-secret",
    )
    monkeypatch.setenv(
        "FRONTEND_BASE_URL",
        "http://frontend.test/",
    )
    monkeypatch.setenv(
        "EMAIL_DELIVERY_MODE",
        "console",
    )
    monkeypatch.setenv(
        "BREVO_API_KEY",
        "test-brevo-api-key",
    )
    monkeypatch.setenv(
        "EMAIL_FROM_ADDRESS",
        "no-reply@example.com",
    )

    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


def test_build_email_verification_url(
    configured_email_settings: None,
) -> None:
    verification_url = build_email_verification_url(
        "test-token",
    )

    assert verification_url == (
        "http://frontend.test/"
        "verify-email?token=test-token"
    )


def test_console_mode_does_not_contact_brevo(
    configured_email_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_post(
        *args: object,
        **kwargs: object,
    ) -> None:
        pytest.fail(
            "El modo console no debe contactar a Brevo.",
        )

    monkeypatch.setattr(
        "app.services.email.httpx.post",
        unexpected_post,
    )

    send_verification_email(
        "learner@example.com",
        "Learner",
        "test-token",
    )


def test_brevo_mode_sends_expected_request(
    configured_email_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "EMAIL_DELIVERY_MODE",
        "brevo",
    )
    get_settings.cache_clear()

    captured_request: dict[str, object] = {}

    def fake_post(
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        captured_request["url"] = url
        captured_request.update(kwargs)

        return httpx.Response(202)

    monkeypatch.setattr(
        "app.services.email.httpx.post",
        fake_post,
    )

    send_verification_email(
        "learner@example.com",
        "Learner",
        "test-token",
    )

    headers = captured_request["headers"]
    payload = captured_request["json"]

    assert isinstance(headers, dict)
    assert isinstance(payload, dict)
    assert headers["api-key"] == "test-brevo-api-key"
    assert payload["to"][0]["email"] == (
        "learner@example.com"
    )


def test_brevo_rejection_raises_delivery_error(
    configured_email_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "EMAIL_DELIVERY_MODE",
        "brevo",
    )
    get_settings.cache_clear()

    def rejected_post(
        *args: object,
        **kwargs: object,
    ) -> httpx.Response:
        return httpx.Response(400)

    monkeypatch.setattr(
        "app.services.email.httpx.post",
        rejected_post,
    )

    with pytest.raises(
        EmailDeliveryError,
        match="400",
    ):
        send_verification_email(
            "learner@example.com",
            "Learner",
            "test-token",
        )