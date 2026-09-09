"""Centralised configuration. Every value is overridable via environment variable
(or a local .env file loaded by pydantic-settings) so the app carries no host-specific code —
see PRD.md §10.2.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "development"

    database_url: str = "sqlite:///./data/planner.db"

    secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    cors_origins: str = "http://localhost:5173"

    log_level: str = "INFO"

    # Login rate limiting (FR-AUTH-7): N failures per window, then lockout.
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_minutes: int = 15

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        # Secure cookies require HTTPS; relaxed only for local development (NFR-6).
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
