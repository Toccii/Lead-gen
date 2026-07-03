from datetime import datetime, timedelta, timezone

import app.email.service as email_service_module
import app.followup.service as followup_service_module
from app.email.reader import InboundMessage
from app.email.sender import SentMessage
from app.followup.service import check_replies, process_followups_and_closeouts
from app.models.campaign import Campaign
from app.models.email_message import EmailMessage, MessageStatus, MessageType
from app.models.lead import Lead, LeadStatus
from app.models.reply import Reply


def _make_campaign(db_session, **overrides) -> Campaign:
    defaults = dict(name="Followup Test", followup_delay_business_days=3, close_after_days=7)
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


def _make_sent_message(db_session, lead: Lead, campaign: Campaign, **overrides) -> EmailMessage:
    defaults = dict(
        lead_id=lead.id,
        campaign_id=campaign.id,
        message_type=MessageType.FIRST,
        subject="Ciao",
        body="Corpo",
        status=MessageStatus.SENT,
        sent_at=datetime.now(timezone.utc),
        graph_conversation_id="conv-1",
        graph_message_id="msg-1",
    )
    defaults.update(overrides)
    message = EmailMessage(**defaults)
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


# --- reply detection (Module 4) ---


def test_check_replies_matches_conversation_and_marks_lead_risposto(db_session, monkeypatch):
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)
    _make_sent_message(db_session, lead, campaign, graph_conversation_id="conv-1")

    inbound = InboundMessage(
        graph_message_id="reply-1",
        graph_conversation_id="conv-1",
        from_address="marco.ferrari@rossimeccanica.it",
        received_at=datetime.now(timezone.utc),
        snippet="Si, sono interessato",
    )
    monkeypatch.setattr(followup_service_module, "fetch_recent_inbox_messages", lambda since: [inbound])

    summary = check_replies(db_session, since=datetime.now(timezone.utc) - timedelta(days=1))

    assert summary == {"messages_checked": 1, "replies_matched": 1, "leads_updated": 1}
    db_session.refresh(lead)
    assert lead.status == LeadStatus.RISPOSTO
    assert db_session.query(Reply).filter_by(graph_message_id="reply-1").count() == 1


def test_check_replies_ignores_messages_from_own_mailbox(db_session, monkeypatch, patch_email_settings):
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)
    _make_sent_message(db_session, lead, campaign, graph_conversation_id="conv-1")

    inbound = InboundMessage(
        graph_message_id="self-copy-1",
        graph_conversation_id="conv-1",
        from_address=patch_email_settings.ms_graph_sender_mailbox,
        received_at=datetime.now(timezone.utc),
        snippet="auto",
    )
    monkeypatch.setattr(followup_service_module, "fetch_recent_inbox_messages", lambda since: [inbound])

    summary = check_replies(db_session, since=datetime.now(timezone.utc) - timedelta(days=1))

    assert summary["replies_matched"] == 0
    db_session.refresh(lead)
    assert lead.status == LeadStatus.INVIATA


def test_check_replies_is_idempotent_on_rerun(db_session, monkeypatch):
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)
    _make_sent_message(db_session, lead, campaign, graph_conversation_id="conv-1")

    inbound = InboundMessage(
        graph_message_id="reply-1",
        graph_conversation_id="conv-1",
        from_address="marco.ferrari@rossimeccanica.it",
        received_at=datetime.now(timezone.utc),
        snippet="ok",
    )
    monkeypatch.setattr(followup_service_module, "fetch_recent_inbox_messages", lambda since: [inbound])

    check_replies(db_session, since=datetime.now(timezone.utc) - timedelta(days=1))
    second_summary = check_replies(db_session, since=datetime.now(timezone.utc) - timedelta(days=1))

    assert second_summary["replies_matched"] == 0
    assert db_session.query(Reply).count() == 1


def test_check_replies_ignores_unmatched_conversation(db_session, monkeypatch):
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA)
    _make_sent_message(db_session, lead, campaign, graph_conversation_id="conv-1")

    inbound = InboundMessage(
        graph_message_id="unrelated-1",
        graph_conversation_id="conv-does-not-exist",
        from_address="someone@example.it",
        received_at=datetime.now(timezone.utc),
        snippet="newsletter",
    )
    monkeypatch.setattr(followup_service_module, "fetch_recent_inbox_messages", lambda since: [inbound])

    summary = check_replies(db_session, since=datetime.now(timezone.utc) - timedelta(days=1))

    assert summary["replies_matched"] == 0


# --- automatic followup (Module 5) ---


def test_process_followups_sends_after_3_business_days(db_session, monkeypatch, patch_email_settings, fake_anthropic):
    monkeypatch.setattr(
        email_service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="fu-1", graph_conversation_id="fu-conv-1"),
    )

    campaign = _make_campaign(db_session, followup_delay_business_days=3, followup_offer_text="Sconto 20%")
    first_contact = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)  # Friday
    now = datetime(2026, 1, 8, 9, 0, tzinfo=timezone.utc)  # exactly 3 IT business days later
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA, first_contacted_at=first_contact)

    summary = process_followups_and_closeouts(db_session, now=now)

    assert summary["followups_sent"] == 1
    db_session.refresh(lead)
    assert lead.status == LeadStatus.FOLLOW_UP_INVIATO


def test_process_followups_skips_before_deadline(db_session, monkeypatch, patch_email_settings, fake_anthropic):
    def _fail_if_called(*a, **k):
        raise AssertionError("must not send before the 3-business-day deadline")

    monkeypatch.setattr(email_service_module, "graph_send_email", _fail_if_called)

    campaign = _make_campaign(db_session, followup_delay_business_days=3)
    first_contact = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    not_yet = datetime(2026, 1, 7, 9, 0, tzinfo=timezone.utc)  # only 2 IT business days elapsed
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA, first_contacted_at=first_contact)

    summary = process_followups_and_closeouts(db_session, now=not_yet)

    assert summary["followups_sent"] == 0
    db_session.refresh(lead)
    assert lead.status == LeadStatus.INVIATA


def test_process_followups_stops_at_rate_limit(db_session, monkeypatch, patch_email_settings, fake_anthropic):
    patch_email_settings.max_emails_per_day = 0

    def _fail_if_called(*a, **k):
        raise AssertionError("graph sender must not be called once rate-limited")

    monkeypatch.setattr(email_service_module, "graph_send_email", _fail_if_called)

    campaign = _make_campaign(db_session, followup_delay_business_days=3)
    first_contact = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    now = datetime(2026, 1, 8, 9, 0, tzinfo=timezone.utc)
    lead = _make_lead(db_session, campaign, status=LeadStatus.INVIATA, first_contacted_at=first_contact)

    summary = process_followups_and_closeouts(db_session, now=now)

    assert summary["rate_limit_hit"] is True
    assert summary["followups_sent"] == 0
    db_session.refresh(lead)
    assert lead.status == LeadStatus.INVIATA


def test_process_followups_never_touches_opted_out_lead(db_session, monkeypatch, patch_email_settings, fake_anthropic):
    # Defensive: a lead can only be INVIATA here, but guard against any future bug that lets an
    # opt-out slip into the INVIATA query by asserting the send path is exercised correctly and
    # opt-out leads are simply absent from the pending set.
    campaign = _make_campaign(db_session)
    _make_lead(db_session, campaign, status=LeadStatus.OPT_OUT, email="optout@rossimeccanica.it")

    summary = process_followups_and_closeouts(db_session, now=datetime(2026, 1, 8, tzinfo=timezone.utc))

    assert summary["followups_sent"] == 0


# --- close-out (Module 5) ---


def test_closeout_after_close_after_days(db_session):
    campaign = _make_campaign(db_session, close_after_days=7)
    lead = _make_lead(db_session, campaign, status=LeadStatus.FOLLOW_UP_INVIATO)
    followup_sent_at = datetime.now(timezone.utc) - timedelta(days=8)
    _make_sent_message(
        db_session,
        lead,
        campaign,
        message_type=MessageType.FOLLOWUP,
        sent_at=followup_sent_at,
        graph_conversation_id="conv-close-1",
        graph_message_id="msg-close-1",
    )

    summary = process_followups_and_closeouts(db_session)

    assert summary["closed_without_response"] == 1
    db_session.refresh(lead)
    assert lead.status == LeadStatus.CHIUSO_SENZA_RISPOSTA


def test_closeout_not_yet_due(db_session):
    campaign = _make_campaign(db_session, close_after_days=7)
    lead = _make_lead(db_session, campaign, status=LeadStatus.FOLLOW_UP_INVIATO)
    followup_sent_at = datetime.now(timezone.utc) - timedelta(days=2)
    _make_sent_message(
        db_session,
        lead,
        campaign,
        message_type=MessageType.FOLLOWUP,
        sent_at=followup_sent_at,
        graph_conversation_id="conv-close-2",
        graph_message_id="msg-close-2",
    )

    summary = process_followups_and_closeouts(db_session)

    assert summary["closed_without_response"] == 0
    db_session.refresh(lead)
    assert lead.status == LeadStatus.FOLLOW_UP_INVIATO
