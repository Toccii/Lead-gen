from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CampaignBase(BaseModel):
    name: str
    is_active: bool = True
    industries: list[str] = Field(default_factory=list)
    company_size_min: int | None = None
    company_size_max: int | None = None
    revenue_min: Decimal | None = None
    revenue_max: Decimal | None = None
    geography: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    max_leads_per_cycle: int = 50
    email_tone_of_voice: str | None = None
    followup_offer_text: str | None = None
    followup_delay_business_days: int = 3
    close_after_days: int = 7


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    industries: list[str] | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    revenue_min: Decimal | None = None
    revenue_max: Decimal | None = None
    geography: list[str] | None = None
    target_roles: list[str] | None = None
    keywords: list[str] | None = None
    max_leads_per_cycle: int | None = None
    email_tone_of_voice: str | None = None
    followup_offer_text: str | None = None
    followup_delay_business_days: int | None = None
    close_after_days: int | None = None


class CampaignRead(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
