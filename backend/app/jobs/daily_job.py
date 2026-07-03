"""Daily job: reply detection + followup/close-out based on business-day deadlines. Invoked by
the hosting platform's cron scheduler as `python -m app.jobs.daily_job` (see Phase 6). Writes an
ExecutionLog row per run.
"""
