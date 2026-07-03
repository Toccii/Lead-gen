from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.lead import Lead


class Reply(TimestampMixin, Base):
    """An inbound reply detected in the mailbox, matched to a lead via Graph conversation id."""

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    email_message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("email_messages.id", ondelete="SET NULL"), nullable=True
    )

    graph_message_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    graph_conversation_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    from_address: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    lead: Mapped["Lead"] = relationship(back_populates="replies")
