from app.core.security import hash_password
from app.models.user import User


def _seed_user(db_session, email="owner@example.it", password="s3cret-pw"):
    user = User(email=email, hashed_password=hash_password(password))
    db_session.add(user)
    db_session.commit()
    return email, password


def test_login_success_returns_token(client, db_session):
    email, password = _seed_user(db_session)
    client.headers.pop("Authorization", None)

    resp = client.post("/auth/login", json={"email": email, "password": password})

    assert resp.status_code == 200
    assert resp.json()["access_token"]
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, db_session):
    email, _ = _seed_user(db_session)
    client.headers.pop("Authorization", None)

    resp = client.post("/auth/login", json={"email": email, "password": "wrong-password"})

    assert resp.status_code == 401


def test_login_unknown_email_returns_401(client):
    client.headers.pop("Authorization", None)
    resp = client.post("/auth/login", json={"email": "nobody@example.it", "password": "x"})
    assert resp.status_code == 401


def test_protected_endpoint_requires_auth(client):
    client.headers.pop("Authorization", None)
    resp = client.get("/campaigns")
    assert resp.status_code == 401


def test_protected_endpoint_rejects_garbage_token(client):
    client.headers["Authorization"] = "Bearer not-a-real-jwt"
    resp = client.get("/campaigns")
    assert resp.status_code == 401


def test_protected_endpoint_works_with_valid_token(client):
    resp = client.get("/campaigns")
    assert resp.status_code == 200


def test_auth_me_returns_current_user(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "test-admin@example.it"


def test_unsubscribe_endpoint_does_not_require_auth(client):
    client.headers.pop("Authorization", None)
    resp = client.get("/unsubscribe/not-a-real-token")
    assert resp.status_code == 400  # rejected for an invalid token, not for missing auth


def test_health_endpoint_does_not_require_auth(client):
    client.headers.pop("Authorization", None)
    resp = client.get("/health")
    assert resp.status_code == 200
