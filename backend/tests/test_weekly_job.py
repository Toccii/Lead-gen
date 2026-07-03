import app.email.service as email_service_module
import app.jobs.weekly_job as weekly_job_module
from app.core.security import create_access_token
from app.email.sender import SentMessage
from app.jobs.weekly_job import run_weekly_job
from app.models.campaign import Campaign
from app.models.execution_log import ExecutionStatus, JobType
from app.models.lead import Lead, LeadStatus


def _make_campaign(db_session, **overrides) -> Campaign:
    defaults = dict(name="Weekly Test", is_active=True, max_leads_per_cycle=3)
    defaults.update(overrides)
    campaign = Campaign(**defaults)
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


def test_run_weekly_job_sources_and_sends_for_active_campaigns(
    db_session, monkeypatch, patch_email_settings, fake_anthropic
):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: True)
    monkeypatch.setattr(
        email_service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="w-1", graph_conversation_id="w-conv-1"),
    )

    campaign = _make_campaign(db_session)

    log = run_weekly_job(db_session)

    assert log is not None
    assert log.job_type == JobType.WEEKLY_SOURCING_AND_SEND
    assert log.status == ExecutionStatus.SUCCESS
    assert log.summary["campaigns_processed"] == 1
    assert log.summary["leads_sourced"] == 3
    assert log.summary["emails_sent"] == 3

    leads = db_session.query(Lead).filter_by(campaign_id=campaign.id).all()
    assert len(leads) == 3
    assert all(lead.status == LeadStatus.INVIATA for lead in leads)


def test_run_weekly_job_skips_inactive_campaigns(db_session, monkeypatch, patch_email_settings, fake_anthropic):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: True)
    _make_campaign(db_session, is_active=False)

    log = run_weekly_job(db_session)

    assert log.summary["campaigns_processed"] == 0
    assert log.summary["emails_sent"] == 0
    assert db_session.query(Lead).count() == 0


def test_run_weekly_job_returns_none_when_not_due_and_not_forced(db_session, monkeypatch):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: False)
    _make_campaign(db_session)

    log = run_weekly_job(db_session)

    assert log is None
    assert db_session.query(Lead).count() == 0


def test_run_weekly_job_force_bypasses_schedule_gate(
    db_session, monkeypatch, patch_email_settings, fake_anthropic
):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: False)
    monkeypatch.setattr(
        email_service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="w-2", graph_conversation_id="w-conv-2"),
    )
    _make_campaign(db_session)

    log = run_weekly_job(db_session, force=True)

    assert log is not None
    assert log.summary["campaigns_processed"] == 1


def test_run_weekly_job_stops_sending_at_rate_limit(
    db_session, monkeypatch, patch_email_settings, fake_anthropic
):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: True)
    patch_email_settings.max_emails_per_day = 1
    monkeypatch.setattr(
        email_service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="w-3", graph_conversation_id="w-conv-3"),
    )

    _make_campaign(db_session, max_leads_per_cycle=3)

    log = run_weekly_job(db_session)

    assert log.summary["rate_limit_hit"] is True
    assert log.summary["emails_sent"] == 1
    assert db_session.query(Lead).filter_by(status=LeadStatus.NUOVO).count() == 2


def test_weekly_job_api_endpoint_forces_execution(client, monkeypatch, patch_email_settings, fake_anthropic):
    monkeypatch.setattr(weekly_job_module, "is_weekly_job_due", lambda db, now=None: False)
    monkeypatch.setattr(
        email_service_module,
        "graph_send_email",
        lambda *a, **k: SentMessage(graph_message_id="w-4", graph_conversation_id="w-conv-4"),
    )
    # patch_email_settings swaps security_module's get_settings *after* `client` signed its
    # token under the real settings; re-sign now so decode_access_token uses the same secret.
    client.headers["Authorization"] = f"Bearer {create_access_token('test-admin@example.it')}"

    resp = client.post("/campaigns", json={"name": "API Weekly Test", "max_leads_per_cycle": 1})
    assert resp.status_code == 201

    resp = client.post("/jobs/weekly-run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_type"] == "weekly_sourcing_and_send"
    assert body["summary"]["campaigns_processed"] == 1
