from unittest.mock import patch

from app.jobs.daily_job import run_followup_job, run_reply_check_job
from app.models.execution_log import ExecutionStatus, JobType


def test_run_reply_check_job_writes_execution_log(db_session):
    with patch("app.jobs.daily_job.check_replies", return_value={"messages_checked": 0, "replies_matched": 0, "leads_updated": 0}):
        log = run_reply_check_job(db_session, force=True)

    assert log.job_type == JobType.DAILY_REPLY_CHECK
    assert log.status == ExecutionStatus.SUCCESS
    assert log.finished_at is not None
    assert log.summary["messages_checked"] == 0


def test_run_reply_check_job_records_failure_without_raising(db_session):
    with patch("app.jobs.daily_job.check_replies", side_effect=RuntimeError("Graph is down")):
        log = run_reply_check_job(db_session, force=True)

    assert log.status == ExecutionStatus.FAILED
    assert "Graph is down" in log.summary["errors"][0]


def test_run_followup_job_writes_execution_log(db_session):
    with patch(
        "app.jobs.daily_job.process_followups_and_closeouts",
        return_value={"followups_sent": 0, "followups_failed": 0, "closed_without_response": 0, "rate_limit_hit": False},
    ):
        log = run_followup_job(db_session, force=True)

    assert log.job_type == JobType.DAILY_FOLLOWUP
    assert log.status == ExecutionStatus.SUCCESS


def test_run_reply_check_job_returns_none_when_not_due_and_not_forced(db_session, monkeypatch):
    monkeypatch.setattr("app.jobs.daily_job.is_daily_job_due", lambda db, now=None: False)
    log = run_reply_check_job(db_session)
    assert log is None


def test_run_followup_job_returns_none_when_not_due_and_not_forced(db_session, monkeypatch):
    monkeypatch.setattr("app.jobs.daily_job.is_daily_job_due", lambda db, now=None: False)
    log = run_followup_job(db_session)
    assert log is None


def test_run_reply_check_job_runs_when_due(db_session, monkeypatch):
    monkeypatch.setattr("app.jobs.daily_job.is_daily_job_due", lambda db, now=None: True)
    with patch("app.jobs.daily_job.check_replies", return_value={"messages_checked": 0, "replies_matched": 0, "leads_updated": 0}):
        log = run_reply_check_job(db_session)
    assert log is not None
    assert log.status == ExecutionStatus.SUCCESS


def test_jobs_api_endpoints_trigger_and_return_execution_log(client):
    # No Graph credentials configured in the test environment, so the reply-check job records
    # a FAILED run rather than raising - the endpoint itself must still respond 200.
    resp = client.post("/jobs/check-replies")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_type"] == "daily_reply_check"
    assert body["status"] == "failed"
    assert body["summary"]["errors"]

    resp = client.post("/jobs/process-followups")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_type"] == "daily_followup"
    assert body["status"] == "success"
