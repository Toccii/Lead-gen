from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.execution_log import ExecutionStatus, JobType


class ExecutionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: JobType
    campaign_id: int | None
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime | None
    summary: dict[str, Any]
