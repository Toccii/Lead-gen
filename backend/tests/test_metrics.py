from datetime import datetime, timedelta, timezone

from app.models.campaign import Campaign
from app.models.email_message import EmailMessage, MessageStatus, MessageType
from app.models.lead import Lead, LeadStatus


def _make_campaign(db_session) -> Campaign:
    campaign = Campaign(name="Metrics Test")
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


def _make_lead(db_session, campaign: Campaign, status: LeadStatus, email_suffix: str) -> Lead:
    lead = Lead(
        campaign_id=campaign.id,
        company_name="Azienda",
        email=f"lead-{email_suffix}@example.it",
        source="mock",
        status=status,
        legal_basis="Legittimo interesse B2B",
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


def test_dashboard_metrics_funnel_and_response_rate(client, db_session):
    campaign = _make_campaign(db_session)
    _make_lead(db_session, campaign, LeadStatus.NUOVO, "1")
    _make_lead(db_session, campaign, LeadStatus.INVIATA, "2")
    _make_lead(db_session, campaign, LeadStatus.INVIATA, "3")
    _make_lead(db_session, campaign, LeadStatus.RISPOSTO, "4")
    _make_lead(db_session, campaign, LeadStatus.CHIUSO_SENZA_RISPOSTA, "5")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_leads"] == 5
    assert body["funnel"]["nuovo"] == 1
    assert body["funnel"]["inviata"] == 2
    assert body["funnel"]["risposto"] == 1
    assert body["funnel"]["chiuso_senza_risposta"] == 1
    # contacted = inviata(2) + risposto(1) + follow_up_inviato(0) + chiuso(1) = 4; responded=1
    assert body["response_rate"] == 0.25


def test_dashboard_metrics_zero_contacted_gives_zero_response_rate(client, db_session):
    campaign = _make_campaign(db_session)
    _make_lead(db_session, campaign, LeadStatus.NUOVO, "1")

    resp = client.get("/metrics")
    assert resp.json()["response_rate"] == 0.0


def test_dashboard_metrics_emails_sent_this_week_excludes_older(client, db_session):
    campaign = _make_campaign(db_session)
    lead = _make_lead(db_session, campaign, LeadStatus.INVIATA, "1")

    db_session.add_all(
        [
            EmailMessage(
                lead_id=lead.id,
                campaign_id=campaign.id,
                message_type=MessageType.FIRST,
                subject="x",
                body="x",
                status=MessageStatus.SENT,
                sent_at=datetime.now(timezone.utc) - timedelta(days=1),
            ),
            EmailMessage(
                lead_id=lead.id,
                campaign_id=campaign.id,
                message_type=MessageType.FIRST,
                subject="x",
                body="x",
                status=MessageStatus.SENT,
                sent_at=datetime.now(timezone.utc) - timedelta(days=10),
            ),
        ]
    )
    db_session.commit()

    resp = client.get("/metrics")
    assert resp.json()["emails_sent_this_week"] == 1
