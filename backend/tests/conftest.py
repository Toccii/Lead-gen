import types

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.security as security_module
import app.email.generator as generator_module
import app.email.service as email_service_module
import app.followup.service as followup_service_module
import app.models  # noqa: F401 - register all models on Base.metadata
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.models.user import User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


TEST_USER_EMAIL = "test-admin@example.it"
TEST_USER_PASSWORD = "test-password"


@pytest.fixture()
def client(db_session):
    """A TestClient pre-authenticated as a seeded test admin user, so tests exercising
    protected endpoints don't need to know about auth. Tests that specifically test the auth
    flow itself can pop the Authorization header or seed their own user."""

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    db_session.add(User(email=TEST_USER_EMAIL, hashed_password=hash_password(TEST_USER_PASSWORD)))
    db_session.commit()

    with TestClient(fastapi_app) as test_client:
        test_client.headers["Authorization"] = f"Bearer {create_access_token(TEST_USER_EMAIL)}"
        yield test_client
    fastapi_app.dependency_overrides.clear()


class FakeSettings:
    def __init__(self):
        self.anthropic_api_key = "test-key"
        self.anthropic_model = "claude-test"
        self.email_dry_run = False
        self.max_emails_per_day = 30
        self.secret_key = "test-secret"
        self.unsubscribe_base_url = "http://localhost:8000/unsubscribe"
        self.ms_graph_sender_mailbox = "outreach@example.it"
        self.jwt_algorithm = "HS256"
        self.jwt_expire_minutes = 1440
        self.dashboard_admin_email = "admin@example.it"
        self.dashboard_admin_password = "test-password"


@pytest.fixture()
def fake_settings():
    return FakeSettings()


@pytest.fixture()
def patch_email_settings(monkeypatch, fake_settings):
    """Shared by tests in app.email and app.followup that need a controllable Settings
    object instead of the real (cached) one - e.g. to set max_emails_per_day=0."""
    monkeypatch.setattr(generator_module, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(email_service_module, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(followup_service_module, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(security_module, "get_settings", lambda: fake_settings)
    return fake_settings


@pytest.fixture()
def fake_anthropic(monkeypatch):
    """Mocks the Anthropic client used by app.email.generator so tests never hit the real API."""

    class _FakeMessages:
        def create(self, **kwargs):
            text = "OGGETTO: Follow-up per Rossi Meccanica\n\nBuongiorno, le scrivo di nuovo."
            return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=text)])

    class _FakeClient:
        def __init__(self, api_key):
            self.messages = _FakeMessages()

    monkeypatch.setattr(generator_module.anthropic, "Anthropic", _FakeClient)
