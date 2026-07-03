from datetime import datetime
from zoneinfo import ZoneInfo

from app.jobs.schedule import get_system_settings, is_daily_job_due, is_weekly_job_due
from app.models.system_settings import SystemSettings

ROME = ZoneInfo("Europe/Rome")


def test_get_system_settings_creates_row_if_missing(db_session):
    settings_row = get_system_settings(db_session)
    assert settings_row.id == 1
    assert db_session.query(SystemSettings).count() == 1


def test_is_weekly_job_due_matches_configured_day_and_hour(db_session):
    get_system_settings(db_session)  # defaults: weekly_job_day_of_week=0 (Monday), hour=8
    monday_8am = datetime(2026, 1, 5, 8, 30, tzinfo=ROME)  # verified Monday
    assert is_weekly_job_due(db_session, now=monday_8am) is True


def test_is_weekly_job_due_false_on_wrong_day(db_session):
    get_system_settings(db_session)
    tuesday_8am = datetime(2026, 1, 6, 8, 30, tzinfo=ROME)  # verified Tuesday
    assert is_weekly_job_due(db_session, now=tuesday_8am) is False


def test_is_weekly_job_due_false_on_wrong_hour(db_session):
    get_system_settings(db_session)
    monday_9am = datetime(2026, 1, 5, 9, 30, tzinfo=ROME)
    assert is_weekly_job_due(db_session, now=monday_9am) is False


def test_is_daily_job_due_matches_configured_hour(db_session):
    get_system_settings(db_session)  # default daily_job_hour=9
    some_day_9am = datetime(2026, 1, 7, 9, 15, tzinfo=ROME)
    assert is_daily_job_due(db_session, now=some_day_9am) is True


def test_is_daily_job_due_false_outside_configured_hour(db_session):
    get_system_settings(db_session)
    some_day_10am = datetime(2026, 1, 7, 10, 15, tzinfo=ROME)
    assert is_daily_job_due(db_session, now=some_day_10am) is False


def test_schedule_respects_updated_settings(db_session):
    settings_row = get_system_settings(db_session)
    settings_row.weekly_job_day_of_week = 2  # Wednesday
    settings_row.weekly_job_hour = 14
    db_session.commit()

    wednesday_2pm = datetime(2026, 1, 7, 14, 0, tzinfo=ROME)  # verified Wednesday
    assert is_weekly_job_due(db_session, now=wednesday_2pm) is True
