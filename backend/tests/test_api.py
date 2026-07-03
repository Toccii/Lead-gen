def test_full_sourcing_flow_via_api(client):
    resp = client.post(
        "/campaigns",
        json={
            "name": "Studi Legali Milano",
            "industries": ["Consulenza legale"],
            "geography": ["Milano"],
            "target_roles": ["Titolare"],
            "keywords": ["contrattualistica"],
            "max_leads_per_cycle": 3,
        },
    )
    assert resp.status_code == 201
    campaign = resp.json()

    resp = client.post(f"/campaigns/{campaign['id']}/source")
    assert resp.status_code == 200
    log = resp.json()
    assert log["status"] == "success"
    assert log["summary"]["created"] == 3

    resp = client.get("/leads", params={"campaign_id": campaign["id"]})
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 3
    assert all(lead["status"] == "nuovo" for lead in leads)
    assert all(lead["legal_basis"] for lead in leads)

    resp = client.get("/execution-logs", params={"campaign_id": campaign["id"]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_campaign_delete_blocked_when_leads_exist(client):
    resp = client.post("/campaigns", json={"name": "Con lead", "max_leads_per_cycle": 1})
    campaign_id = resp.json()["id"]
    client.post(f"/campaigns/{campaign_id}/source")

    resp = client.delete(f"/campaigns/{campaign_id}")
    assert resp.status_code == 409


def test_campaign_delete_allowed_when_no_leads(client):
    resp = client.post("/campaigns", json={"name": "Senza lead", "max_leads_per_cycle": 0})
    campaign_id = resp.json()["id"]

    resp = client.delete(f"/campaigns/{campaign_id}")
    assert resp.status_code == 204


def test_campaign_update_partial(client):
    resp = client.post("/campaigns", json={"name": "Da aggiornare"})
    campaign_id = resp.json()["id"]

    resp = client.put(f"/campaigns/{campaign_id}", json={"max_leads_per_cycle": 10})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["max_leads_per_cycle"] == 10
    assert updated["name"] == "Da aggiornare"
