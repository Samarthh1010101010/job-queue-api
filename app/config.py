import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = "Job Queue & Status API"
    app_version: str = "0.2.0"
    app_phase: int = 1
    environment: str = "production"

    # Default to async SQLite if DATABASE_URL is not provided (for local dev/testing)
    database_url: str = "sqlite+aiosqlite:///./job_queue.db"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
