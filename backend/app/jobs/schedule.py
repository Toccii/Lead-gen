"""Dashboard-configurable schedule gate.

The hosting platform's cron fires the weekly/daily job scripts frequently (recommended:
hourly - see README) rather than at one fixed cron expression per setting. This module decides
whether "now" actually matches the day/hour configured in the `system_settings` table (edited
from the dashboard), so changing the schedule never requires touching the platform's cron
config - only editing a row in the dashboard.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.system_settings import SystemSettings

_ROME_TZ = ZoneInfo("Europe/Rome")


def get_system_settings(db: Session) -> SystemSettings:
    settings_row = db.get(SystemSettings, 1)
    if settings_row is None:
        # Should already exist (seeded by the initial migration) - created defensively here so
        # a fresh/non-migrated dev DB still works.
        settings_row = SystemSettings(id=1)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def is_weekly_job_due(db: Session, now: datetime | None = None) -> bool:
    now = (now or datetime.now(_ROME_TZ)).astimezone(_ROME_TZ)
    settings_row = get_system_settings(db)
    return now.weekday() == settings_row.weekly_job_day_of_week and now.hour == settings_row.weekly_job_hour


def is_daily_job_due(db: Session, now: datetime | None = None) -> bool:
    now = (now or datetime.now(_ROME_TZ)).astimezone(_ROME_TZ)
    settings_row = get_system_settings(db)
    return now.hour == settings_row.daily_job_hour
