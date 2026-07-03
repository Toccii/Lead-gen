from app.core.security import build_unsubscribe_token
from app.models.lead import Lead
from app.models.suppression import Suppression


def test_unsubscribe_flow_marks_lead_opt_out_and_suppresses_email(client, db_session):
    resp = client.post("/campaigns", json={"name": "Unsub Test", "max_leads_per_cycle": 1})
    campaign_id = resp.json()["id"]
    resp = client.post(f"/campaigns/{campaign_id}/source")
    assert resp.json()["summary"]["created"] == 1

    lead_id = client.get("/leads", params={"campaign_id": campaign_id}).json()[0]["id"]
    lead_email = db_session.get(Lead, lead_id).email

    token = build_unsubscribe_token(lead_id)
    resp = client.get(f"/unsubscribe/{token}")
    assert resp.status_code == 200
    assert lead_email in resp.text

    db_session.expire_all()
    lead = db_session.get(Lead, lead_id)
    assert lead.status.value == "opt_out"
    assert db_session.query(Suppression).filter_by(email=lead_email).count() == 1


def test_unsubscribe_invalid_token_returns_400(client):
    resp = client.get("/unsubscribe/not-a-real-token")
    assert resp.status_code == 400


def test_unsubscribe_tampered_token_returns_400(client):
    token = build_unsubscribe_token(1)
    tampered = token[:-1] + ("0" if token[-1] != "0" else "1")
    resp = client.get(f"/unsubscribe/{tampered}")
    assert resp.status_code == 400
