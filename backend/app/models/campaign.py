from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.lead import Lead


class Campaign(TimestampMixin, Base):
    """ICP (Ideal Customer Profile) config for a lead-gen campaign. Editable from the dashboard."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Targeting criteria
    industries: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    company_size_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_size_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue_min: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    revenue_max: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    geography: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    max_leads_per_cycle: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # Email copy configuration
    email_tone_of_voice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    followup_offer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    followup_delay_business_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    close_after_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)

    leads: Mapped[list["Lead"]] = relationship(back_populates="campaign")
