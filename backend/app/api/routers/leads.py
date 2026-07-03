from __future__ import annotations

from datetime import datetime

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
    industry: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[Lead]:
    stmt = select(Lead).order_by(Lead.id.desc())
    if campaign_id is not None:
        stmt = stmt.where(Lead.campaign_id == campaign_id)
    if status is not None:
        stmt = stmt.where(Lead.status == status)
    if industry is not None:
        stmt = stmt.where(Lead.industry.ilike(f"%{industry}%"))
    if created_after is not None:
        stmt = stmt.where(Lead.created_at >= created_after)
    if created_before is not None:
        stmt = stmt.where(Lead.created_at <= created_before)
    return list(db.scalars(stmt))
