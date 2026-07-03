def test_leads_filter_by_industry(client):
    resp = client.post(
        "/campaigns", json={"name": "Filter Test", "industries": ["Moda"], "max_leads_per_cycle": 3}
    )
    campaign_id = resp.json()["id"]
    client.post(f"/campaigns/{campaign_id}/source")

    resp = client.get("/leads", params={"industry": "Moda"})
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp = client.get("/leads", params={"industry": "Nonexistent"})
    assert resp.json() == []


def test_leads_filter_by_created_after_excludes_older_leads(client):
    resp = client.post("/campaigns", json={"name": "Date Filter Test", "max_leads_per_cycle": 2})
    campaign_id = resp.json()["id"]
    client.post(f"/campaigns/{campaign_id}/source")

    resp = client.get("/leads", params={"created_after": "2999-01-01T00:00:00Z"})
    assert resp.json() == []

    resp = client.get("/leads", params={"created_before": "2999-01-01T00:00:00Z"})
    assert len(resp.json()) == 2
