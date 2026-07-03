"""Runs a sourcing pass for a campaign: calls the configured LeadSource, dedupes results
against existing leads and the global suppression list, persists new leads with status
`nuovo`, and records an ExecutionLog row for the run.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.campaign import Campaign
from app.models.execution_log import ExecutionLog, ExecutionStatus, JobType
from app.models.lead import DEFAULT_LEGAL_BASIS, Lead, LeadStatus
from app.models.suppression import Suppression
from app.sourcing.apollo import ApolloLeadSource
from app.sourcing.base import ICPCriteria, LeadSource, SourcedLead
from app.sourcing.mock import MockLeadSource


def _get_source(adapter_name: str) -> LeadSource:
    if adapter_name == "apollo":
        return ApolloLeadSource()
    return MockLeadSource()


def campaign_to_icp_criteria(campaign: Campaign) -> ICPCriteria:
    return ICPCriteria(
        industries=campaign.industries,
        geography=campaign.geography,
        target_roles=campaign.target_roles,
        keywords=campaign.keywords,
        company_size_min=campaign.company_size_min,
        company_size_max=campaign.company_size_max,
    )


def _process_sourced_lead(
    db: Session, campaign: Campaign, source_name: str, sourced: SourcedLead, summary: dict[str, Any]
) -> None:
    email = (sourced.email or "").strip().lower() or None
    if not email:
        summary["skipped_no_email"] += 1
        return

    if db.scalar(select(Suppression.id).where(Suppression.email == email)):
        summary["skipped_suppressed"] += 1
        return

    if db.scalar(select(Lead.id).where(Lead.email == email)):
        summary["skipped_duplicate"] += 1
        return

    if db.scalar(
        select(Lead.id).where(
            Lead.company_name == sourced.company_name,
            Lead.contact_first_name == sourced.contact_first_name,
            Lead.contact_last_name == sourced.contact_last_name,
        )
    ):
        summary["skipped_duplicate"] += 1
        return

    lead = Lead(
        campaign_id=campaign.id,
        company_name=sourced.company_name,
        contact_first_name=sourced.contact_first_name,
        contact_last_name=sourced.contact_last_name,
        role_title=sourced.role_title,
        email=email,
        website=sourced.website,
        linkedin_company_url=sourced.linkedin_company_url,
        industry=sourced.industry,
        company_size=sourced.company_size,
        source=source_name,
        source_id=sourced.source_id,
        status=LeadStatus.NUOVO,
        legal_basis=DEFAULT_LEGAL_BASIS,
    )
    db.add(lead)
    summary["created"] += 1


def run_sourcing(
    db: Session,
    campaign: Campaign,
    job_type: JobType = JobType.MANUAL,
    adapter_name: str | None = None,
) -> ExecutionLog:
    settings = get_settings()
    adapter_name = adapter_name or settings.sourcing_adapter
    source = _get_source(adapter_name)

    log = ExecutionLog(
        job_type=job_type,
        campaign_id=campaign.id,
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        summary={},
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    summary: dict[str, Any] = {
        "adapter": source.name,
        "requested": campaign.max_leads_per_cycle,
        "sourced": 0,
        "created": 0,
        "skipped_no_email": 0,
        "skipped_duplicate": 0,
        "skipped_suppressed": 0,
        "errors": [],
    }

    try:
        criteria = campaign_to_icp_criteria(campaign)
        sourced_leads = source.search(criteria, campaign.max_leads_per_cycle)
        summary["sourced"] = len(sourced_leads)

        for sourced in sourced_leads:
            _process_sourced_lead(db, campaign, source.name, sourced, summary)

        db.commit()
        log.status = ExecutionStatus.SUCCESS
    except Exception as exc:  # noqa: BLE001 - job-runner boundary, must record failure, not crash
        db.rollback()
        summary["errors"].append(str(exc))
        log.status = ExecutionStatus.FAILED

    log.finished_at = datetime.now(timezone.utc)
    log.summary = summary
    db.commit()
    db.refresh(log)
    return log
