import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


def test_user_create_normalizes_input() -> None:
    user = UserCreate(
        email="  Learner@EXAMPLE.COM ",
        password="safe-learning-password",
        display_name="  Learner  ",
        country_code="mx",
    )

    assert str(user.email) == "learner@example.com"
    assert user.display_name == "Learner"
    assert user.country_code == "MX"


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="learner@example.com",
            password="short",
            display_name="Learner",
        )


def test_user_create_rejects_invalid_country_code() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="learner@example.com",
            password="safe-learning-password",
            display_name="Learner",
            country_code="MEX",
        )