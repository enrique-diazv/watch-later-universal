from functools import lru_cache

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
    database_password: SecretStr

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
@lru_cache
def get_settings() -> Settings:
    return Settings()