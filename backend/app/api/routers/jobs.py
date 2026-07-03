from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.jobs.daily_job import run_followup_job, run_reply_check_job
from app.schemas.execution_log import ExecutionLogRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/check-replies", response_model=ExecutionLogRead)
def trigger_reply_check(db: Session = Depends(get_db)) -> ExecutionLogRead:
    return run_reply_check_job(db)


@router.post("/process-followups", response_model=ExecutionLogRead)
def trigger_followups(db: Session = Depends(get_db)) -> ExecutionLogRead:
    return run_followup_job(db)
