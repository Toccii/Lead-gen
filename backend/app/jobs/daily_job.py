"""Daily job: reply detection + followup/close-out based on business-day deadlines.

Invoked by the hosting platform's cron scheduler as `python -m app.jobs.daily_job` - see
README for the recommended cron wiring on Railway/Render. Gated by `app.jobs.schedule` so the
cron itself can fire hourly while the actual hour stays editable from the dashboard
(`system_settings` table) without touching the platform's cron config.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.followup.service import check_replies, process_followups_and_closeouts
from app.jobs.schedule import is_daily_job_due
from app.models.execution_log import ExecutionLog, ExecutionStatus, JobType

# Re-checks a window wider than one day, so a missed or delayed run doesn't lose replies.
REPLY_CHECK_LOOKBACK = timedelta(days=14)


def _start_log(db: Session, job_type: JobType) -> ExecutionLog:
    log = ExecutionLog(
        job_type=job_type,
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


def run_reply_check_job(db: Session, force: bool = False) -> ExecutionLog | None:
    if not force and not is_daily_job_due(db):
        return None

    log = _start_log(db, JobType.DAILY_REPLY_CHECK)
    try:
        since = datetime.now(timezone.utc) - REPLY_CHECK_LOOKBACK
        summary = check_replies(db, since)
        _finish_log(db, log, ExecutionStatus.SUCCESS, summary)
    except Exception as exc:  # noqa: BLE001 - job-runner boundary, must record failure, not crash
        db.rollback()
        _finish_log(db, log, ExecutionStatus.FAILED, {"errors": [str(exc)]})
    return log


def run_followup_job(db: Session, force: bool = False) -> ExecutionLog | None:
    if not force and not is_daily_job_due(db):
        return None

    log = _start_log(db, JobType.DAILY_FOLLOWUP)
    try:
        summary = process_followups_and_closeouts(db)
        _finish_log(db, log, ExecutionStatus.SUCCESS, summary)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _finish_log(db, log, ExecutionStatus.FAILED, {"errors": [str(exc)]})
    return log


def main() -> None:
    db = SessionLocal()
    try:
        run_reply_check_job(db)
        run_followup_job(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
