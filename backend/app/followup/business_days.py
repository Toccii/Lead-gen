"""Italian business-day arithmetic (Mon-Fri, excluding Italian public holidays) used to
schedule the followup email (default: 3 business days after first contact) and to check
the close-out deadline (default: N calendar days after the followup).

Dates are computed in Europe/Rome, not UTC, so a "business day" lines up with the Italian
calendar even though timestamps are stored in UTC.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import holidays

_IT_HOLIDAYS = holidays.country_holidays("IT")
_ROME_TZ = ZoneInfo("Europe/Rome")


def to_rome_date(dt: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_ROME_TZ).date()


def is_italian_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _IT_HOLIDAYS


def add_business_days(start: date, business_days: int) -> date:
    """Returns the date `business_days` Italian business days after `start`."""
    current = start
    remaining = business_days
    while remaining > 0:
        current += timedelta(days=1)
        if is_italian_business_day(current):
            remaining -= 1
    return current


def business_days_elapsed(start: datetime, now: datetime) -> int:
    """Counts Italian business days strictly between `start` and `now` (both converted to
    Europe/Rome dates). Same-day returns 0.
    """
    start_date = to_rome_date(start)
    now_date = to_rome_date(now)
    if now_date <= start_date:
        return 0

    count = 0
    current = start_date
    while current < now_date:
        current += timedelta(days=1)
        if is_italian_business_day(current):
            count += 1
    return count
