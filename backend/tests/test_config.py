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
