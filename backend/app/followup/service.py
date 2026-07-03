"""Daily reply-detection and followup/close-out processing.

Reply detection (Module 4) is mailbox-wide: it fetches recent inbox messages and matches them
to sent conversations regardless of campaign. Followup/close-out (Module 5) is per-lead, using
each lead's own campaign for timing (business days) and offer text.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.email.reader import fetch_recent_inbox_messages
from app.email.service import RateLimitExceeded, send_email_to_lead
from app.followup.business_days import business_days_elapsed
from app.models.campaign import Campaign
from app.models.email_message import EmailMessage, MessageStatus, MessageType
from app.models.lead import Lead, LeadStatus
from app.models.reply import Reply

_REPLYABLE_STATUSES = (LeadStatus.INVIATA, LeadStatus.FOLLOW_UP_INVIATO)


def _as_aware_utc(dt: datetime) -> datetime:
    """SQLite (used in tests) drops tzinfo on round-trip even for DateTime(timezone=True)
    columns; Postgres does not. Normalize so date arithmetic works the same on both."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def check_replies(db: Session, since: datetime) -> dict[str, Any]:
    settings = get_settings()
    summary: dict[str, Any] = {"messages_checked": 0, "replies_matched": 0, "leads_updated": 0}

    inbound_messages = fetch_recent_inbox_messages(since)
    summary["messages_checked"] = len(inbound_messages)

    for inbound in inbound_messages:
        if not inbound.graph_conversation_id:
            continue
        if settings.ms_graph_sender_mailbox and inbound.from_address == settings.ms_graph_sender_mailbox:
            continue  # defensive: never treat our own sent copy as a reply
        if db.scalar(select(Reply.id).where(Reply.graph_message_id == inbound.graph_message_id)):
            continue  # already recorded on a previous run

        sent_message = db.scalar(
            select(EmailMessage).where(
                EmailMessage.graph_conversation_id == inbound.graph_conversation_id,
                EmailMessage.status == MessageStatus.SENT,
            )
        )
        if sent_message is None:
            continue

        summary["replies_matched"] += 1
        db.add(
            Reply(
                lead_id=sent_message.lead_id,
                email_message_id=sent_message.id,
                graph_message_id=inbound.graph_message_id,
                graph_conversation_id=inbound.graph_conversation_id,
                from_address=inbound.from_address,
                snippet=inbound.snippet,
                received_at=inbound.received_at,
            )
        )

        lead = db.get(Lead, sent_message.lead_id)
        if lead is not None and lead.status in _REPLYABLE_STATUSES:
            lead.status = LeadStatus.RISPOSTO
            lead.last_status_change_at = datetime.now(timezone.utc)
            summary["leads_updated"] += 1

    db.commit()
    return summary


def process_followups_and_closeouts(db: Session, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    settings = get_settings()
    summary: dict[str, Any] = {
        "followups_sent": 0,
        "followups_failed": 0,
        "closed_without_response": 0,
        "rate_limit_hit": False,
    }

    pending = db.scalars(select(Lead).where(Lead.status == LeadStatus.INVIATA)).all()
    for lead in pending:
        if lead.first_contacted_at is None:
            continue
        campaign = db.get(Campaign, lead.campaign_id)
        if campaign is None:
            continue
        if business_days_elapsed(lead.first_contacted_at, now) < campaign.followup_delay_business_days:
            continue

        try:
            send_email_to_lead(db, lead, campaign, MessageType.FOLLOWUP, dry_run=settings.email_dry_run)
            summary["followups_sent"] += 1
        except RateLimitExceeded:
            summary["rate_limit_hit"] = True
            break
        except Exception:  # noqa: BLE001 - one bad lead must not stop the rest of the run
            summary["followups_failed"] += 1

    closeable = db.scalars(select(Lead).where(Lead.status == LeadStatus.FOLLOW_UP_INVIATO)).all()
    for lead in closeable:
        campaign = db.get(Campaign, lead.campaign_id)
        if campaign is None:
            continue

        last_followup = db.scalar(
            select(EmailMessage)
            .where(
                EmailMessage.lead_id == lead.id,
                EmailMessage.message_type == MessageType.FOLLOWUP,
                EmailMessage.status == MessageStatus.SENT,
            )
            .order_by(EmailMessage.sent_at.desc())
        )
        reference_time = last_followup.sent_at if last_followup else lead.last_status_change_at
        if reference_time is None:
            continue
        reference_time = _as_aware_utc(reference_time)

        if now - reference_time >= timedelta(days=campaign.close_after_days):
            lead.status = LeadStatus.CHIUSO_SENZA_RISPOSTA
            lead.last_status_change_at = now
            summary["closed_without_response"] += 1

    db.commit()
    return summary
