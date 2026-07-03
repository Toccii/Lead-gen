from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.jobs.daily_job import run_followup_job, run_reply_check_job
from app.jobs.weekly_job import run_weekly_job
from app.schemas.execution_log import ExecutionLogRead

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Manual triggers always run immediately - the dashboard-configured schedule gate only applies
# to the platform cron invocation (see app.jobs.schedule).


@router.post("/check-replies", response_model=ExecutionLogRead)
def trigger_reply_check(db: Session = Depends(get_db)) -> ExecutionLogRead:
    return run_reply_check_job(db, force=True)


@router.post("/process-followups", response_model=ExecutionLogRead)
def trigger_followups(db: Session = Depends(get_db)) -> ExecutionLogRead:
    return run_followup_job(db, force=True)


@router.post("/weekly-run", response_model=ExecutionLogRead)
def trigger_weekly_run(db: Session = Depends(get_db)) -> ExecutionLogRead:
    return run_weekly_job(db, force=True)
