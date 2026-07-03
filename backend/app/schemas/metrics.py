from __future__ import annotations

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    total_leads: int
    emails_sent_this_week: int
    response_rate: float
    funnel: dict[str, int]
