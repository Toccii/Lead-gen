"""Weekly job: sourcing + first-email send for each active campaign. Invoked by the hosting
platform's cron scheduler as `python -m app.jobs.weekly_job` (see Phase 6). Writes an
ExecutionLog row per run.
"""
