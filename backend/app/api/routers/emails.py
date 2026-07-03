from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.email.service import InvalidLeadStateError, RateLimitExceeded, send_email_to_lead
from app.models.campaign import Campaign
from app.models.email_message import MessageType
from app.models.lead import Lead
from app.schemas.email_message import EmailMessageRead

router = APIRouter(prefix="/leads", tags=["email"])


@router.post("/{lead_id}/send-email", response_model=EmailMessageRead)
def send_email_endpoint(
    lead_id: int,
    message_type: MessageType = MessageType.FIRST,
    dry_run: bool = Query(
        True, description="If true (default), generates and logs the email but never calls Microsoft Graph"
    ),
    db: Session = Depends(get_db),
) -> EmailMessageRead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    campaign = db.get(Campaign, lead.campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found for this lead")

    try:
        return send_email_to_lead(db, lead, campaign, message_type, dry_run=dry_run)
    except InvalidLeadStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
