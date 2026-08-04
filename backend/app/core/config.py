from functools import lru_cache
from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tmdb_access_token: SecretStr
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_language: str = "es-MX"
    tmdb_region: str = "MX"

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "watch_later"
    database_user: str = "watch_later_app"
    database_password: SecretStr | None = None
    database_url: SecretStr | None = None

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    email_verification_token_expire_hours: int = 24
    email_verification_resend_cooldown_seconds: int = 60
    password_reset_token_expire_minutes: int = 30
    password_reset_request_cooldown_seconds: int = 60
    frontend_base_url: str = "http://localhost:5173"
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    email_delivery_mode: Literal[
        "console",
        "brevo",
    ] = "console"

    brevo_api_url: str = "https://api.brevo.com/v3/smtp/email"
    brevo_api_key: SecretStr | None = None

    email_from_address: str = "no-reply@watch-later.local"
    email_from_name: str = "Watch Later Universal"
    email_request_timeout_seconds: float = 10.0
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_samesite: Literal[
        "lax",
        "strict",
        "none",
    ] = "lax"
    refresh_cookie_secure: bool = False
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
