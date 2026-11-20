"""
Tests for Authentication, Password Hashing, JWT Tokens, and Server-side RBAC.
Verifies that citizens cannot access Officer or Admin endpoints (HTTP 403).
"""
from fastapi.testclient import TestClient


def test_login_demo_citizen(client: TestClient):
    """Verifies login for pre-seeded citizen account."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "citizen_parveen",
        "password": "password123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "citizen"
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    """Verifies 401 on incorrect password."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "citizen_parveen",
        "password": "wrongpassword"
    })
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_token_refresh(client: TestClient):
    """Verifies refresh token exchange for a new access token."""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "citizen_parveen",
        "password": "password123"
    })
    refresh_tok = login_resp.json()["refresh_token"]

    ref_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_tok})
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()


def test_rbac_citizen_forbidden_on_officer_endpoint(client: TestClient, citizen_headers: dict):
    """
    CRITICAL SECURITY CHECK:
    A citizen attempting to access the Officer Review Queue MUST receive HTTP 403 Forbidden.
    """
    resp = client.get("/api/v1/review/queue", headers=citizen_headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "RBAC_FORBIDDEN"
    assert "officer" in resp.json()["detail"]["required_roles"]


def test_rbac_officer_allowed_on_officer_endpoint(client: TestClient, officer_headers: dict):
    """Verifies that an Officer can access the Review Queue."""
    resp = client.get("/api/v1/review/queue", headers=officer_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rbac_citizen_forbidden_on_admin_rules_publish(client: TestClient, citizen_headers: dict):
    """Verifies that a citizen cannot publish or alter rules."""
    resp = client.post("/api/v1/rules/publish", json={
        "version": 99,
        "name": "Unauthorized Rule",
        "max_monthly_income": 999999.0
    }, headers=citizen_headers)
    assert resp.status_code == 403
