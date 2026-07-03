from datetime import date, datetime, timezone

from app.followup.business_days import (
    add_business_days,
    business_days_elapsed,
    is_italian_business_day,
)


def test_is_italian_business_day_flags_holidays_and_weekends():
    assert is_italian_business_day(date(2026, 1, 5)) is True  # Monday, no holiday
    assert is_italian_business_day(date(2026, 1, 1)) is False  # Capodanno (Thursday)
    assert is_italian_business_day(date(2026, 1, 6)) is False  # Epifania (Tuesday)
    assert is_italian_business_day(date(2026, 1, 3)) is False  # Saturday
    assert is_italian_business_day(date(2026, 1, 4)) is False  # Sunday


def test_add_business_days_skips_weekend_and_holiday():
    # Fri 2026-01-02 + 3 business days: skip Sat/Sun, skip Epifania (Tue Jan 6) -> Thu Jan 8
    start = date(2026, 1, 2)
    assert add_business_days(start, 3) == date(2026, 1, 8)


def test_business_days_elapsed_matches_add_business_days():
    start = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    exactly_3_days_later = datetime(2026, 1, 8, 9, 0, tzinfo=timezone.utc)
    not_yet = datetime(2026, 1, 7, 9, 0, tzinfo=timezone.utc)

    assert business_days_elapsed(start, exactly_3_days_later) == 3
    assert business_days_elapsed(start, not_yet) == 2


def test_business_days_elapsed_same_day_is_zero():
    start = datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc)
    later_same_day = datetime(2026, 1, 5, 18, 0, tzinfo=timezone.utc)
    assert business_days_elapsed(start, later_same_day) == 0
