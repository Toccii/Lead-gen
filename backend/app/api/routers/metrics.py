from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.email_message import EmailMessage, MessageStatus
from app.models.lead import Lead, LeadStatus
from app.schemas.metrics import DashboardMetrics

router = APIRouter(prefix="/metrics", tags=["metrics"])

_CONTACTED_STATUSES = (
    LeadStatus.INVIATA,
    LeadStatus.RISPOSTO,
    LeadStatus.FOLLOW_UP_INVIATO,
    LeadStatus.CHIUSO_SENZA_RISPOSTA,
)


@router.get("", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetrics:
    total_leads = db.scalar(select(func.count()).select_from(Lead)) or 0

    funnel = {status.value: 0 for status in LeadStatus}
    for status_value, count in db.execute(select(Lead.status, func.count()).group_by(Lead.status)).all():
        funnel[status_value.value] = count

    since_week = datetime.now(timezone.utc) - timedelta(days=7)
    emails_sent_this_week = (
        db.scalar(
            select(func.count())
            .select_from(EmailMessage)
            .where(EmailMessage.status == MessageStatus.SENT, EmailMessage.sent_at >= since_week)
        )
        or 0
    )

    contacted = sum(funnel[s.value] for s in _CONTACTED_STATUSES)
    responded = funnel[LeadStatus.RISPOSTO.value]
    response_rate = round(responded / contacted, 4) if contacted else 0.0

    return DashboardMetrics(
        total_leads=total_leads,
        emails_sent_this_week=emails_sent_this_week,
        response_rate=response_rate,
        funnel=funnel,
    )
