def test_get_system_settings_returns_defaults(client):
    resp = client.get("/system-settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["weekly_job_day_of_week"] == 0
    assert body["weekly_job_hour"] == 8
    assert body["daily_job_hour"] == 9
    assert body["max_emails_per_day"] == 30


def test_update_system_settings_partial(client):
    resp = client.put(
        "/system-settings",
        json={"weekly_job_day_of_week": 2, "weekly_job_hour": 14},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["weekly_job_day_of_week"] == 2
    assert body["weekly_job_hour"] == 14
    assert body["daily_job_hour"] == 9  # untouched

    resp = client.get("/system-settings")
    assert resp.json()["weekly_job_day_of_week"] == 2


def test_update_system_settings_rejects_out_of_range_hour(client):
    resp = client.put("/system-settings", json={"weekly_job_hour": 24})
    assert resp.status_code == 422


def test_update_system_settings_rejects_out_of_range_day(client):
    resp = client.put("/system-settings", json={"weekly_job_day_of_week": 7})
    assert resp.status_code == 422


def test_system_settings_requires_auth(client):
    client.headers.pop("Authorization", None)
    resp = client.get("/system-settings")
    assert resp.status_code == 401
