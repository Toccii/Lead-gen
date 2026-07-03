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
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app


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


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
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
