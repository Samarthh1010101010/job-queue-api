from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = "Job Queue & Status API"
    app_version: str = "0.3.0"
    app_phase: int = 2

    # PostgreSQL — CI uses the Postgres service container at this default.
    # Production overrides via the DATABASE_URL env var (e.g. Neon PostgreSQL).
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Phase 2 — Service Bus (empty = skip sending gracefully)
    service_bus_connection_string: str = ""
    service_bus_queue_name: str = "jobs"

    # Phase 4 — Application Insights (empty = skip instrumentation)
    appinsights_connection_string: str = ""


settings = Settings()
