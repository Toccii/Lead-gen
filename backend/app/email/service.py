"""Orchestrates one outreach email: generates the copy via Claude, persists an EmailMessage
row, enforces the daily send-rate limit, and - unless dry_run - sends via Microsoft Graph and
advances the lead's status. Shared by the manual test endpoint (Phase 3) and the weekly/daily
jobs (Phase 6).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.email.generator import generate_email
from app.email.sender import send_email as graph_send_email
from app.models.campaign import Campaign
from app.models.email_message import EmailMessage, MessageStatus, MessageType
from app.models.lead import Lead, LeadStatus

_EXPECTED_STATUS_FOR_MESSAGE_TYPE = {
    MessageType.FIRST: LeadStatus.NUOVO,
    MessageType.FOLLOWUP: LeadStatus.INVIATA,
}
_LEAD_STATUS_AFTER_SEND = {
    MessageType.FIRST: LeadStatus.INVIATA,
    MessageType.FOLLOWUP: LeadStatus.FOLLOW_UP_INVIATO,
}


class RateLimitExceeded(RuntimeError):
    pass


class InvalidLeadStateError(ValueError):
    pass


def emails_sent_today(db: Session) -> int:
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.scalar(
        select(func.count())
        .select_from(EmailMessage)
        .where(EmailMessage.status == MessageStatus.SENT, EmailMessage.sent_at >= since)
    )
    return count or 0


def send_email_to_lead(
    db: Session,
    lead: Lead,
    campaign: Campaign,
    message_type: MessageType,
    dry_run: bool | None = None,
) -> EmailMessage:
    settings = get_settings()
    dry_run = settings.email_dry_run if dry_run is None else dry_run

    if lead.status == LeadStatus.OPT_OUT:
        raise InvalidLeadStateError(f"Lead {lead.id} has opted out and can never be contacted again")

    expected_status = _EXPECTED_STATUS_FOR_MESSAGE_TYPE[message_type]
    if lead.status != expected_status:
        raise InvalidLeadStateError(
            f"Lead {lead.id} has status '{lead.status.value}', expected '{expected_status.value}' "
            f"to send a '{message_type.value}' email"
        )

    content = generate_email(campaign, lead, message_type)

    message = EmailMessage(
        lead_id=lead.id,
        campaign_id=campaign.id,
        message_type=message_type,
        subject=content.subject,
        body=content.body,
        status=MessageStatus.DRAFT,
        dry_run=dry_run,
    )
    db.add(message)

    if dry_run:
        db.commit()
        db.refresh(message)
        return message

    if emails_sent_today(db) >= settings.max_emails_per_day:
        message.status = MessageStatus.FAILED
        message.error_detail = "Daily send rate limit reached"
        db.commit()
        db.refresh(message)
        raise RateLimitExceeded(f"Daily limit of {settings.max_emails_per_day} emails reached")

    try:
        sent = graph_send_email(lead.email, content.subject, content.body)
    except Exception as exc:  # noqa: BLE001 - persist as failed, let the caller move to the next lead
        message.status = MessageStatus.FAILED
        message.error_detail = str(exc)
        db.commit()
        db.refresh(message)
        return message

    now = datetime.now(timezone.utc)
    message.status = MessageStatus.SENT
    message.graph_message_id = sent.graph_message_id
    message.graph_conversation_id = sent.graph_conversation_id
    message.sent_at = now

    lead.status = _LEAD_STATUS_AFTER_SEND[message_type]
    lead.last_status_change_at = now
    if message_type == MessageType.FIRST:
        lead.first_contacted_at = now

    db.commit()
    db.refresh(message)
    return message
