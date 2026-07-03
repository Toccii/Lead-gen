from app.models.campaign import Campaign
from app.models.execution_log import ExecutionStatus, JobType
from app.models.lead import Lead
from app.models.suppression import Suppression
from app.sourcing.base import ICPCriteria
from app.sourcing.mock import MockLeadSource
from app.sourcing.service import campaign_to_icp_criteria, run_sourcing


def _make_campaign(db_session, **overrides) -> Campaign:
    defaults = dict(
        name="Test Campaign",
        industries=["Manifattura"],
        geography=["Lombardia"],
        target_roles=["Titolare", "HR Manager"],
        keywords=["automazione"],
        max_leads_per_cycle=5,
    )
    defaults.update(overrides)
    campaign = Campaign(**defaults)
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    return campaign


def test_mock_source_generates_leads_matching_limit():
    source = MockLeadSource()
    criteria = ICPCriteria(industries=["Manifattura"], target_roles=["Titolare"])
    leads = source.search(criteria, limit=5)

    assert len(leads) == 5
    assert all(lead.email for lead in leads)
    assert all(lead.company_name for lead in leads)


def test_mock_source_is_deterministic():
    source = MockLeadSource()
    criteria = ICPCriteria(industries=["Manifattura"], target_roles=["Titolare"])

    first_run = source.search(criteria, limit=5)
    second_run = source.search(criteria, limit=5)

    assert [lead.email for lead in first_run] == [lead.email for lead in second_run]


def test_run_sourcing_creates_leads_with_status_nuovo_and_legal_basis(db_session):
    campaign = _make_campaign(db_session)

    log = run_sourcing(db_session, campaign, job_type=JobType.MANUAL, adapter_name="mock")

    assert log.status == ExecutionStatus.SUCCESS
    assert log.summary["created"] == 5
    leads = db_session.query(Lead).all()
    assert len(leads) == 5
    assert all(lead.status.value == "nuovo" for lead in leads)
    assert all(lead.legal_basis for lead in leads)
    assert all(lead.source == "mock" for lead in leads)


def test_run_sourcing_dedupes_on_second_run(db_session):
    campaign = _make_campaign(db_session)

    run_sourcing(db_session, campaign, adapter_name="mock")
    second_log = run_sourcing(db_session, campaign, adapter_name="mock")

    assert second_log.summary["created"] == 0
    assert second_log.summary["skipped_duplicate"] == 5
    assert db_session.query(Lead).count() == 5


def test_run_sourcing_skips_suppressed_email(db_session):
    campaign = _make_campaign(db_session)
    criteria = campaign_to_icp_criteria(campaign)
    first_sourced_lead = MockLeadSource().search(criteria, limit=1)[0]

    db_session.add(Suppression(email=first_sourced_lead.email, reason="opt_out_link"))
    db_session.commit()

    log = run_sourcing(db_session, campaign, adapter_name="mock")

    assert log.summary["skipped_suppressed"] == 1
    assert log.summary["created"] == 4
    assert db_session.query(Lead).filter_by(email=first_sourced_lead.email).count() == 0
