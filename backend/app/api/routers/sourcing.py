from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.execution_log import JobType
from app.schemas.execution_log import ExecutionLogRead
from app.sourcing.service import run_sourcing

router = APIRouter(prefix="/campaigns", tags=["sourcing"])


@router.post("/{campaign_id}/source", response_model=ExecutionLogRead)
def trigger_sourcing(campaign_id: int, db: Session = Depends(get_db)) -> ExecutionLogRead:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return run_sourcing(db, campaign, job_type=JobType.MANUAL)
