from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.lead import Lead


class MessageType(str, enum.Enum):
    FIRST = "first"
    FOLLOWUP = "followup"


class MessageStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"


class EmailMessage(TimestampMixin, Base):
    """Log of every outbound email (first contact or followup) sent via Microsoft Graph."""

    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)

    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType, name="message_type"), nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status"), default=MessageStatus.DRAFT, nullable=False
    )
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    graph_message_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    graph_conversation_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship(back_populates="email_messages")
