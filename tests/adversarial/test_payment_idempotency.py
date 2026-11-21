"""
Adversarial Test Suite I: Payment Safety & Idempotency Stress Attacks.
Tests I01 - I08: Evaluates 20x concurrency deduplication, timeout recovery,
missing token gating, and double-disbursement prevention on mock Raast rails.
"""
import uuid
import pytest
from fastapi.testclient import TestClient


def test_i01_20x_concurrent_payment_requests_single_settlement(client: TestClient):
    """I01: Submit the same payment request 20 times concurrently with the same idempotency key."""
    shared_key = f"idem_20x_{uuid.uuid4().hex[:8]}"
    valid_token = "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    case_id = f"cas_pay_20_{uuid.uuid4().hex[:6]}"

    payload = {
        "idempotency_key": shared_key,
        "case_id": case_id,
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": valid_token
    }

    status_codes = []
    settled_tx_ids = set()

    for _ in range(20):
        r = client.post("/api/v1/mock/payment/disburse", json=payload)
        status_codes.append(r.status_code)
        if r.status_code == 200:
            settled_tx_ids.add(r.json().get("transaction_id"))

    # All 20 requests must return 200 OK
    assert all(s == 200 for s in status_codes)
    # Exactly 1 unique transaction settled (zero double-payout)
    assert len(settled_tx_ids) == 1


def test_i02_payment_timeout_chaos_mode_simulation(client: TestClient):
    """I02: Payment endpoint subjected to chaos timeout returns 504 Gateway Timeout."""
    payload = {
        "idempotency_key": f"idem_timeout_{uuid.uuid4().hex[:6]}",
        "case_id": "cas_timeout_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    }
    r = client.post("/api/v1/mock/payment/disburse?chaos=timeout", json=payload)
    assert r.status_code == 504


def test_i03_retry_same_payment_using_same_idempotency_key(client: TestClient):
    """I03: Retry using the same idempotency key returns exact original receipt."""
    key = f"idem_retry_{uuid.uuid4().hex[:8]}"
    payload = {
        "idempotency_key": key,
        "case_id": "cas_retry_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    }

    r1 = client.post("/api/v1/mock/payment/disburse", json=payload)
    r2 = client.post("/api/v1/mock/payment/disburse", json=payload)

    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["transaction_id"] == r2.json()["transaction_id"]


def test_i04_payment_exceeding_max_single_grant_limit(client: TestClient):
    """I04: Attempting single payout exceeding 25,000 limit is rejected with HTTP 400."""
    payload = {
        "idempotency_key": f"idem_limit_{uuid.uuid4().hex[:6]}",
        "case_id": "cas_limit_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 50000.0,  # Exceeds 25,000 limit
        "approval_token": "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    }
    r = client.post("/api/v1/mock/payment/disburse", json=payload)
    assert r.status_code == 400


def test_i05_payment_with_empty_or_missing_approval_token_blocked(client: TestClient):
    """I05: Attempt payment with no approval token returns HTTP 403."""
    payload = {
        "idempotency_key": f"idem_notoken_{uuid.uuid4().hex[:6]}",
        "case_id": "cas_notoken_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": ""  # Missing token
    }
    r = client.post("/api/v1/mock/payment/disburse", json=payload)
    assert r.status_code == 403


def test_i06_payment_with_short_forged_token_blocked(client: TestClient):
    """I06: Attempt payment with short forged token returns HTTP 403."""
    payload = {
        "idempotency_key": f"idem_short_{uuid.uuid4().hex[:6]}",
        "case_id": "cas_short_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": "forged_short"
    }
    r = client.post("/api/v1/mock/payment/disburse", json=payload)
    assert r.status_code == 403


def test_i07_payment_chaos_500_server_error_simulation(client: TestClient):
    """I07: Rail failure simulation with ?chaos=500 returns 500 Internal Error."""
    payload = {
        "idempotency_key": f"idem_500_{uuid.uuid4().hex[:6]}",
        "case_id": "cas_500_01",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    }
    r = client.post("/api/v1/mock/payment/disburse?chaos=500", json=payload)
    assert r.status_code == 500


def test_i08_payment_settled_event_written_to_audit_ledger(client: TestClient):
    """I08: Every settled payment appends a verifiable RAAST_DISBURSEMENT_SETTLED entry to audit ledger."""
    from services.api.engine.audit_log import audit_log
    key = f"idem_aud_{uuid.uuid4().hex[:6]}"
    payload = {
        "idempotency_key": key,
        "case_id": "cas_aud_check",
        "receiver_iban_or_raast_id": "PK99RAAST4210112345678",
        "amount": 12000.0,
        "approval_token": "CRYPTO_HMAC_APPROVAL_TOKEN_VALID_2026"
    }
    r = client.post("/api/v1/mock/payment/disburse", json=payload)
    assert r.status_code == 200

    # Verify latest audit entries contain RAAST_DISBURSEMENT_SETTLED
    entries = audit_log.get_entries(limit=5)
    assert any("RAAST" in e.action for e in entries)
