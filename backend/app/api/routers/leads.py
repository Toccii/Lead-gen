from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadRead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadRead])
def list_leads(
    campaign_id: int | None = None,
    status: LeadStatus | None = None,
    db: Session = Depends(get_db),
) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.id.desc())
    if campaign_id is not None:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    if status is not None:
        stmt = stmt.where(Lead.status == status)
    return list(db.scalars(stmt))
