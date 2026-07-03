import types

import pytest

from app.core.security import build_unsubscribe_token, verify_unsubscribe_token
from app.email import generator as generator_module
from app.email import sender as sender_module
from app.email import service as service_module
from app.email.sender import SentMessage
from app.email.service import InvalidLeadStateError, RateLimitExceeded, send_email_to_lead
from app.models.campaign import Campaign
from app.models.email_message import EmailMessage, MessageStatus, MessageType
from app.models.lead import Lead, LeadStatus


class _FakeSettings:
    anthropic_api_key = "test-key"
    anthropic_model = "claude-test"
    email_dry_run = True
    max_emails_per_day = 30
    secret_key = "test-secret"
    unsubscribe_base_url = "http://localhost:8000/unsubscribe"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    fake = _FakeSettings()
    monkeypatch.setattr(generator_module, "get_settings", lambda: fake)
    monkeypatch.setattr(service_module, "get_settings", lambda: fake)
    return fake


@pytest.fixture()
def _fake_anthropic(monkeypatch):
    captured = {}

    class _FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            text = "OGGETTO: Una proposta per Rossi Meccanica\n\nBuongiorno, corpo del messaggio di prova."
            return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=text)])

    class _FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.messages = _FakeMessages()

    monkeypatch.setattr(generator_module.anthropic, "Anthropic", _FakeClient)
    return captured


def _make_campaign(db_session, **overrides) -> Campaign:
    defaults = dict(name="Test Campaign", email_tone_of_voice="diretto e informale")
    defaults.update(overrides)
    campaign = Campaign(**defaults)
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


def _make_lead(db_session, campaign: Campaign, **overrides) -> Lead:
    defaults = dict(
        campaign_id=campaign.id,
        company_name="Rossi Meccanica",
        contact_first_name="Marco",
        contact_last_name="Ferrari",
        email="marco.ferrari@rossimeccanica.it",
        source="mock",
        status=LeadStatus.NUOVO,
        legal_basis="Legittimo interesse B2B",
    )
    defaults.update(overrides)
    lead = Lead(**defaults)
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


def test_unsubscribe_token_roundtrip(_patch_settings, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _patch_settings)
    token = build_unsubscribe_token(42)
    assert verify_unsubscribe_token(token) == 42
    assert verify_unsubscribe_token(token + "tampered") is None
    assert verify_unsubscribe_token("not-a-token") is None


def test_generate_email_includes_unsubscribe_link(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign)

    content = generator_module.generate_email(campaign, lead, MessageType.FIRST)

    assert "Rossi Meccanica" in content.subject
    assert "http://localhost:8000/unsubscribe/" in content.body
    assert str(lead.id) in content.body


def test_send_email_dry_run_does_not_call_graph_or_change_lead_status(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("Graph sender must not be called in dry-run mode")

    monkeypatch.setattr(service_module, "graph_send_email", _fail_if_called)

    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign)

    message = send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=True)

    assert message.dry_run is True
    assert message.status == MessageStatus.DRAFT
    assert message.sent_at is None
    db_session.refresh(lead)
    assert lead.status == LeadStatus.NUOVO


def test_send_email_real_send_updates_lead_and_message(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(
        service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="msg-1", graph_conversation_id="conv-1"),
    )

    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign)

    message = send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=False)

    assert message.status == MessageStatus.SENT
    assert message.graph_message_id == "msg-1"
    assert message.graph_conversation_id == "conv-1"
    assert message.sent_at is not None
    db_session.refresh(lead)
    assert lead.status == LeadStatus.INVIATA
    assert lead.first_contacted_at is not None


def test_send_followup_updates_lead_to_follow_up_inviato(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(
        service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="msg-2", graph_conversation_id="conv-2"),
    )

    campaign = _make_campaign(db_session, followup_offer_text="Sconto 20% sul primo mese")
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)

    message = send_email_to_lead(db_session, lead, campaign, MessageType.FOLLOWUP, dry_run=False)

    assert message.status == MessageStatus.SENT
    db_session.refresh(lead)
    assert lead.status == LeadStatus.FOLLOW_UP_INVIATO


def test_send_email_wrong_lead_state_raises(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)

    with pytest.raises(InvalidLeadStateError):
        send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=True)


def test_send_email_opt_out_lead_always_raises(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.OPT_OUT)

    with pytest.raises(InvalidLeadStateError):
        send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=True)


def test_rate_limit_exceeded_marks_message_failed_and_stops_send(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())

    from datetime import datetime, timezone

    limited_settings = _FakeSettings()
    limited_settings.max_emails_per_day = 1
    monkeypatch.setattr(service_module, "get_settings", lambda: limited_settings)

    campaign = _make_campaign(db_session)
    already_sent_lead = _make_lead(
        db_session, campaign, email="already@rossimeccanica.it", status=LeadStatus.NUOVO
    )
    db_session.add(
        EmailMessage(
            lead_id=already_sent_lead.id,
            campaign_id=campaign.id,
            message_type=MessageType.FIRST,
            subject="x",
            body="x",
            status=MessageStatus.SENT,
            sent_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("Graph sender must not be called once the rate limit is reached")

    monkeypatch.setattr(service_module, "graph_send_email", _fail_if_called)

    lead = _make_lead(db_session, campaign, email="second@rossimeccanica.it")

    with pytest.raises(RateLimitExceeded):
        send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=False)

    db_session.refresh(lead)
    assert lead.status == LeadStatus.NUOVO
    failed = db_session.query(EmailMessage).filter_by(lead_id=lead.id).one()
    assert failed.status == MessageStatus.FAILED


def test_send_email_graph_failure_marks_message_failed_without_raising(db_session, _fake_anthropic, monkeypatch):
    monkeypatch.setattr("app.core.security.get_settings", lambda: _FakeSettings())

    def _boom(*args, **kwargs):
        raise sender_module.GraphAuthError("token acquisition failed")

    monkeypatch.setattr(service_module, "graph_send_email", _boom)

    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign)

    message = send_email_to_lead(db_session, lead, campaign, MessageType.FIRST, dry_run=False)

    assert message.status == MessageStatus.FAILED
    assert "token acquisition failed" in message.error_detail
    db_session.refresh(lead)
    assert lead.status == LeadStatus.NUOVO
