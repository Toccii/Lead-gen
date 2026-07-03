"""Weekly job: sourcing + first-email send for each active campaign.

Invoked by the hosting platform's cron scheduler as `python -m app.jobs.weekly_job` - see
README for the recommended cron wiring on Railway/Render. Gated by `app.jobs.schedule` so the
cron itself can fire hourly while the actual day/hour stays editable from the dashboard
(`system_settings` table) without touching the platform's cron config.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.email.service import RateLimitExceeded, send_email_to_lead
from app.jobs.schedule import is_weekly_job_due
from app.models.campaign import Campaign
from app.models.email_message import MessageType
from app.models.execution_log import ExecutionLog, ExecutionStatus, JobType
from app.models.lead import Lead, LeadStatus
from app.sourcing.service import run_sourcing


def _start_log(db: Session) -> ExecutionLog:
    log = ExecutionLog(
        job_type=JobType.WEEKLY_SOURCING_AND_SEND,
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        summary={},
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _finish_log(db: Session, log: ExecutionLog, status: ExecutionStatus, summary: dict) -> None:
    log.status = status
    log.summary = summary
    log.finished_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(log)


def run_weekly_job(db: Session, force: bool = False) -> ExecutionLog | None:
    """Runs sourcing then first-send for every active campaign. Returns None (no ExecutionLog
    written) if `force` is False and the configured schedule says it isn't time yet."""
    if not force and not is_weekly_job_due(db):
        return None

    settings = get_settings()
    log = _start_log(db)
    summary: dict[str, Any] = {
        "campaigns_processed": 0,
        "leads_sourced": 0,
        "emails_sent": 0,
        "emails_failed": 0,
        "rate_limit_hit": False,
        "errors": [],
    }

    try:
        campaigns = db.scalars(select(Campaign).where(Campaign.is_active.is_(True))).all()
        for campaign in campaigns:
            sourcing_log = run_sourcing(db, campaign, job_type=JobType.WEEKLY_SOURCING_AND_SEND)
            summary["campaigns_processed"] += 1
            summary["leads_sourced"] += sourcing_log.summary.get("created", 0)
            if sourcing_log.status == ExecutionStatus.FAILED:
                summary["errors"].extend(sourcing_log.summary.get("errors", []))

        pending_leads = db.scalars(select(Lead).where(Lead.status == LeadStatus.NUOVO)).all()
        for lead in pending_leads:
            campaign = db.get(Campaign, lead.campaign_id)
            if campaign is None or not campaign.is_active:
                continue
            try:
                send_email_to_lead(db, lead, campaign, MessageType.FIRST, dry_run=settings.email_dry_run)
                summary["emails_sent"] += 1
            except RateLimitExceeded:
                summary["rate_limit_hit"] = True
                break
            except Exception as exc:  # noqa: BLE001 - one bad lead must not stop the rest of the run
                summary["emails_failed"] += 1
                summary["errors"].append(f"lead {lead.id}: {exc}")

        status = ExecutionStatus.PARTIAL if summary["errors"] else ExecutionStatus.SUCCESS
        _finish_log(db, log, status, summary)
    except Exception as exc:  # noqa: BLE001 - job-runner boundary, must record failure, not crash
        db.rollback()
        summary["errors"] = [str(exc)]
        _finish_log(db, log, ExecutionStatus.FAILED, summary)

    return log


def main() -> None:
    db = SessionLocal()
    try:
        run_weekly_job(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
