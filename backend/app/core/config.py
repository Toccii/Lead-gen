from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Database
    database_url: str = "postgresql+psycopg://leadgen:leadgen@localhost:5432/leadgen"

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Railway/Render/Heroku-style platforms expose DATABASE_URL as `postgres://` or
        `postgresql://`, without a driver suffix. SQLAlchemy needs `postgresql+psycopg://`
        (we use the psycopg v3 driver) - normalize automatically so the platform's raw
        connection string can be pasted in as-is."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    # Dashboard auth
    secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    dashboard_admin_email: str = "you@yourcompany.com"
    dashboard_admin_password: str = "change-me"

    # Apollo.io sourcing
    apollo_api_key: str | None = None
    sourcing_adapter: str = "mock"  # mock | apollo | (future: registro_imprese, google_cse)

    # Anthropic (email copy generation)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    # Microsoft Graph (Outlook / Microsoft 365)
    ms_graph_tenant_id: str | None = None
    ms_graph_client_id: str | None = None
    ms_graph_client_secret: str | None = None
    ms_graph_sender_mailbox: str | None = None
    ms_graph_auth_mode: str = "application"

    # Email sending behavior
    email_dry_run: bool = True
    # Served directly by the backend (GET /unsubscribe/{token}), not by the dashboard frontend,
    # so opt-out keeps working even before/without the dashboard being deployed.
    unsubscribe_base_url: str = "http://localhost:8000/unsubscribe"

    # Rate limiting & scheduling defaults (overridable via system_settings table)
    max_emails_per_day: int = 30
    weekly_job_day_of_week: int = 0  # 0=Monday
    weekly_job_hour: int = 8
    daily_job_hour: int = 9
    timezone: str = "Europe/Rome"

    # Dashboard frontend origin, used to restrict CORS outside of development.
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
