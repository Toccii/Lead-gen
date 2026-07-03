from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.execution_log import ExecutionLog
from app.schemas.execution_log import ExecutionLogRead

router = APIRouter(prefix="/execution-logs", tags=["execution-logs"])


@router.get("", response_model=list[ExecutionLogRead])
def list_execution_logs(campaign_id: int | None = None, db: Session = Depends(get_db)) -> list[ExecutionLog]:
    stmt = select(ExecutionLog).order_by(ExecutionLog.id.desc())
    if campaign_id is not None:
        stmt = stmt.where(ExecutionLog.campaign_id == campaign_id)
    return list(db.scalars(stmt))
