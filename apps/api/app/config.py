from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://heladeria:heladeria@localhost:5432/heladeria"
    direct_database_url: str | None = None
    app_origin: str = "http://localhost:3000"
    session_cookie_name: str = "heladeria_session"
    session_cookie_secure: bool = True
    session_days: int = 30
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4
    vercel_blob_read_write_token: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

