from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SystemSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    max_emails_per_day: int
    weekly_job_day_of_week: int
    weekly_job_hour: int
    daily_job_hour: int
    timezone: str
    default_followup_delay_business_days: int
    default_close_after_days: int


class SystemSettingsUpdate(BaseModel):
    max_emails_per_day: int | None = Field(default=None, ge=1)
    weekly_job_day_of_week: int | None = Field(default=None, ge=0, le=6)
    weekly_job_hour: int | None = Field(default=None, ge=0, le=23)
    daily_job_hour: int | None = Field(default=None, ge=0, le=23)
    default_followup_delay_business_days: int | None = Field(default=None, ge=1)
    default_close_after_days: int | None = Field(default=None, ge=1)
