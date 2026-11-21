"""Tests for the API‑key security utilities and HTTP endpoints.
These tests exercise:
- Core ORM model and helper functions.
- HTTP endpoints: no key 401, valid key 200, revoked key 401.
- Role checks: citizen token creating a key 403, admin token creating a key 200.
- Secret safety: plaintext key never stored or returned by list endpoint.
"""

import hashlib
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the project's DB utilities and the API‑key helpers.
from db.connection import Base
from services.api.security.api_key import (
    KEY_PREFIX,
    _hash_key,
    create_api_key,
    generate_plaintext_key,
)


# ---------------------------------------------------------------------------
# Fixture – a clean in‑memory SQLite DB for unit test functions.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session():
    # Ensure we use an isolated in‑memory DB.
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Helper – verify that a stored hash matches the plaintext key.
# ---------------------------------------------------------------------------
def assert_hash_matches(plain: str, stored_hash: str) -> bool:
    return stored_hash == hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Test the creation function returns a plaintext key and stores only the hash.
# ---------------------------------------------------------------------------
def test_create_api_key_returns_plaintext_and_stores_hash(db_session):
    name = "unit‑test‑key"
    api_key_obj = create_api_key(db_session, name=name)

    # The function should attach the plaintext key as a private attribute.
    plaintext = getattr(api_key_obj, "_plain", None)
    assert plaintext is not None, "Plaintext key not attached"
    assert plaintext.startswith(KEY_PREFIX), "Plaintext key must start with the configured prefix"

    # The stored prefix should match the first characters of the plaintext.
    expected_prefix = plaintext[: len(KEY_PREFIX)]
    assert api_key_obj.key_prefix == expected_prefix

    # The stored hash must correspond to the full plaintext.
    assert assert_hash_matches(plaintext, api_key_obj.key_hash)

    # Basic field checks.
    assert api_key_obj.name == name
    assert api_key_obj.is_active() is True
    assert isinstance(api_key_obj.created_at, datetime)


# ---------------------------------------------------------------------------
# Test that ``_hash_key`` produces the same SHA‑256 hash used by the model.
# ---------------------------------------------------------------------------
def test_hash_key_consistency():
    sample = generate_plaintext_key()
    direct = hashlib.sha256(sample.encode("utf-8")).hexdigest()
    assert _hash_key(sample) == direct


# ---------------------------------------------------------------------------
# Ensure that revoking a key makes ``is_active`` return ``False``.
# ---------------------------------------------------------------------------
def test_api_key_revocation(db_session):
    api_key_obj = create_api_key(db_session, name="revocation-test")
    # Revoke by setting ``revoked_at``.
    api_key_obj.revoked_at = datetime.utcnow()
    db_session.add(api_key_obj)
    db_session.commit()
    assert api_key_obj.is_active() is False


# ---------------------------------------------------------------------------
# HTTP Endpoint Tests
# ---------------------------------------------------------------------------
def test_public_endpoint_no_key_401(client: TestClient):
    """Calling public endpoint without X-API-Key must return 401 Unauthorized."""
    resp = client.get("/api/v1/public/health")
    assert resp.status_code == 401
    assert "Missing API key" in resp.json()["detail"]


def test_public_endpoint_invalid_key_401(client: TestClient):
    """Calling public endpoint with an invalid key must return 401."""
    resp = client.get("/api/v1/public/health", headers={"X-API-Key": f"{KEY_PREFIX}invalidkey12345"})
    assert resp.status_code == 401
    assert "Invalid or revoked API key" in resp.json()["detail"]


def test_citizen_cannot_create_key_403(client: TestClient, citizen_headers: dict):
    """Citizen role must get 403 Forbidden when attempting to create an API key."""
    resp = client.post(
        "/api/v1/admin/api-keys",
        headers=citizen_headers,
        json={"name": "citizen-attempt"},
    )
    assert resp.status_code == 403


def test_admin_create_use_and_revoke_key_lifecycle(client: TestClient, admin_headers: dict):
    """Full lifecycle: Admin creates key (200), uses key (200), revokes key (200), and key is blocked (401)."""
    # 1. Admin creates key
    create_resp = client.post(
        "/api/v1/admin/api-keys",
        headers=admin_headers,
        json={"name": "partner-service-test"},
    )
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert "id" in data
    assert "key" in data
    plaintext_key = data["key"]
    key_id = data["id"]
    assert plaintext_key.startswith(KEY_PREFIX)

    # 2. Use key on public health endpoint
    health_resp = client.get("/api/v1/public/health", headers={"X-API-Key": plaintext_key})
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
    assert health_resp.json()["api_key_name"] == "partner-service-test"

    # 3. Use key on public scam-check endpoint
    scam_resp = client.post(
        "/api/v1/public/scam-check",
        headers={"X-API-Key": plaintext_key},
        json={"text": "Congratulations, you won 50,000 rupees under Benazir scheme. Send 2000 fee."},
    )
    assert scam_resp.status_code == 200
    assert scam_resp.json()["label"] in ["scam", "suspicious", "legitimate"]

    # 4. List keys: verify plaintext is never returned in list endpoint
    list_resp = client.get("/api/v1/admin/api-keys", headers=admin_headers)
    assert list_resp.status_code == 200
    listed_keys = list_resp.json()
    matched = [k for k in listed_keys if k["id"] == key_id]
    assert len(matched) == 1
    # Ensure masked_key contains asterisks and never the full plaintext
    assert "*" in matched[0]["masked_key"]
    assert "key" not in matched[0]

    # 5. Revoke the key
    revoke_resp = client.post(f"/api/v1/admin/api-keys/{key_id}/revoke", headers=admin_headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "revoked"

    # 6. Subsequent requests with revoked key must return 401
    blocked_resp = client.get("/api/v1/public/health", headers={"X-API-Key": plaintext_key})
    assert blocked_resp.status_code == 401
    assert "Invalid or revoked API key" in blocked_resp.json()["detail"]
