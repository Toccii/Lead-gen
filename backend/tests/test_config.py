import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_normalizes_postgres_scheme():
    settings = Settings(database_url="postgres://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_database_url_normalizes_postgresql_scheme_without_driver():
    settings = Settings(database_url="postgresql://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_database_url_leaves_explicit_driver_untouched():
    settings = Settings(database_url="postgresql+psycopg://user:pw@host:5432/db")
    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_database_url_leaves_sqlite_untouched():
    settings = Settings(database_url="sqlite:////tmp/test.db")
    assert settings.database_url == "sqlite:////tmp/test.db"


def test_localhost_database_url_allowed_in_development():
    # Default environment is "development" - the local-dev default DATABASE_URL must not raise.
    settings = Settings(environment="development")
    assert "localhost" in settings.database_url


def test_localhost_database_url_rejected_outside_development():
    with pytest.raises(ValidationError, match="DATABASE_URL is missing or not reaching"):
        Settings(environment="production")


def test_127_0_0_1_database_url_rejected_outside_development():
    with pytest.raises(ValidationError, match="DATABASE_URL is missing or not reaching"):
        Settings(environment="production", database_url="postgresql+psycopg://u:p@127.0.0.1:5432/db")


def test_real_database_url_accepted_outside_development():
    settings = Settings(environment="production", database_url="postgresql://u:p@real-host.railway.internal:5432/db")
    assert "localhost" not in settings.database_url
    assert "127.0.0.1" not in settings.database_url
