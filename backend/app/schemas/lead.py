from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.lead import LeadStatus


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    company_name: str
    contact_first_name: str | None
    contact_last_name: str | None
    role_title: str | None
    email: str | None
    website: str | None
    linkedin_company_url: str | None
    industry: str | None
    company_size: int | None
    source: str
    status: LeadStatus
    legal_basis: str
    created_at: datetime
