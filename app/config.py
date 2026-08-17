from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_title: str = "Job Queue & Status API"
    app_version: str = "0.2.0"
    app_phase: int = 1

    # PostgreSQL — CI uses the Postgres service container at this default.
    # Production overrides via the DATABASE_URL env var set in Azure App Service.
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Phase 2 — Service Bus (empty = skip sending)
    service_bus_connection_string: str = ""

    # Phase 4 — Application Insights (empty = skip instrumentation)
    appinsights_connection_string: str = ""


settings = Settings()
