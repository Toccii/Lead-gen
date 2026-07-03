from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class JobType(str, enum.Enum):
    WEEKLY_SOURCING_AND_SEND = "weekly_sourcing_and_send"
    DAILY_REPLY_CHECK = "daily_reply_check"
    DAILY_FOLLOWUP = "daily_followup"
    MANUAL = "manual"


class ExecutionStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ExecutionLog(TimestampMixin, Base):
    """Audit trail of every scheduled/manual job run, shown in the dashboard."""

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType, name="job_type"), nullable=False)
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, name="execution_status"), default=ExecutionStatus.RUNNING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Free-form counts/details, e.g. {"leads_sourced": 12, "emails_sent": 10, "errors": []}
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
