from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.email_message import EmailMessage
    from app.models.reply import Reply


class LeadStatus(str, enum.Enum):
    NUOVO = "nuovo"
    INVIATA = "inviata"
    RISPOSTO = "risposto"
    FOLLOW_UP_INVIATO = "follow_up_inviato"
    CHIUSO_SENZA_RISPOSTA = "chiuso_senza_risposta"
    OPT_OUT = "opt_out"


DEFAULT_LEGAL_BASIS = (
    "Legittimo interesse B2B (art. 6.1.f GDPR) - contatto email professionale "
    "legato al ruolo aziendale del destinatario, nessun dato personale eccedente"
)


class Lead(TimestampMixin, Base):
    """A single prospect sourced for a campaign. Deduped by email and by company+contact name."""

    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_company_contact", "company_name", "contact_first_name", "contact_last_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, nullable=True, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    linkedin_company_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    source: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "apollo", "mock"
    source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"), default=LeadStatus.NUOVO, nullable=False, index=True
    )
    legal_basis: Mapped[str] = mapped_column(Text, default=DEFAULT_LEGAL_BASIS, nullable=False)

    first_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status_change_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="leads")
    email_messages: Mapped[list["EmailMessage"]] = relationship(back_populates="lead")
    replies: Mapped[list["Reply"]] = relationship(back_populates="lead")
