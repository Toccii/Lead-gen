from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SystemSettings(TimestampMixin, Base):
    """Single-row table of dashboard-editable operational settings (rate limits, schedule times).
    Row id is always 1; seeded by the initial migration with defaults from .env.
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    max_emails_per_day: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    weekly_job_day_of_week: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0=Monday
    weekly_job_hour: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    daily_job_hour: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Rome", nullable=False)
    default_followup_delay_business_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    default_close_after_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
