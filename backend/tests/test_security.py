from app.core.security import (
    hash_password,
    verify_password,
)


def test_hash_password_uses_argon2_and_random_salt() -> None:
    password = "learning-only-password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash.startswith("$argon2")
    assert second_hash.startswith("$argon2")
    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password(
        "learning-only-password",
    )

    assert (
        verify_password(
            "wrong-password",
            password_hash,
        )
        is False
    )