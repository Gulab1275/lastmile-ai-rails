"""
Mission 8A.3 — Adversarial Remediation & Verification Test Suite.
Validates:
1. Cryptographic Key Separation:
   - SECRET_KEY (JWT), APPROVAL_TOKEN_SECRET (HMAC approval tokens), and AUDIT_CHECKPOINT_KEY (checkpoint HMAC)
   - Cross-key rejection: JWT key cannot validate approval tokens, and vice versa.
   - Checkpoint signatures strictly require AUDIT_CHECKPOINT_KEY.
   - Fail-closed behavior on missing or identical secrets.
   - Key rotation verification.
2. Explicit Granular Consent Enforcement:
   - Case creation alone does NOT grant DOCUMENTS consent.
   - Document attachment fails closed (403) without explicit DOCUMENTS authorization.
   - Explicit citizen consent allows attachment (200).
   - Consent withdrawal immediately blocks subsequent attachments (403).
   - Helper and officer unauthorized upload attempts are blocked (403).
3. Audit Ledger Clean Isolation and Concurrency:
   - Clean database initializes valid Genesis block.
   - Multi-threaded concurrent appends produce an unbroken SHA-256 chain.
"""
import os
import threading
import uuid
import pytest
from fastapi.testclient import TestClient
import jwt

from services.api.config import Settings, settings
from services.api.engine.audit_log import AuditLogLedger, audit_log, calculate_hash
from services.api.engine.consent_gateway import consent_gateway
from services.api.engine.decision_engine import generate_approval_token, verify_approval_token
from services.api.main import app
from services.api.security.auth import create_access_token
from services.shared.schemas import ConsentScope, RoleEnum


# ==============================================================================
# 1. TASK 1: CRYPTOGRAPHIC KEY SEPARATION TESTS
# ==============================================================================

def test_approval_token_fails_closed_when_secret_missing(monkeypatch):
    """Approval token generation must fail closed when APPROVAL_TOKEN_SECRET is missing."""
    monkeypatch.delenv("APPROVAL_TOKEN_SECRET", raising=False)
    monkeypatch.setattr(settings, "APPROVAL_TOKEN_SECRET", None)
    with pytest.raises(RuntimeError) as excinfo:
        generate_approval_token("case_123", 1, 0.95)
    assert "APPROVAL_TOKEN_SECRET is not configured" in str(excinfo.value)
    assert "Silent fallback to SECRET_KEY is strictly prohibited" in str(excinfo.value)


def test_approval_token_fails_closed_when_identical_to_jwt_secret(monkeypatch):
    """Key separation: APPROVAL_TOKEN_SECRET cannot be identical to SECRET_KEY."""
    monkeypatch.setenv("APPROVAL_TOKEN_SECRET", settings.SECRET_KEY)
    with pytest.raises(RuntimeError) as excinfo:
        generate_approval_token("case_123", 1, 0.95)
    assert "Cryptographic key separation violation" in str(excinfo.value)


def test_jwt_key_cannot_validate_approval_token(monkeypatch):
    """An approval token generated with APPROVAL_TOKEN_SECRET cannot be verified with SECRET_KEY."""
    token = generate_approval_token("case_test_cross", 1, 0.92)

    # Attempt verification using a forged token generated with SECRET_KEY
    import hashlib, hmac
    forged_token = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"case_test_cross:1:0.9200".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    assert token != forged_token, "Approval token must not match token signed with JWT SECRET_KEY"
    assert verify_approval_token(token, "case_test_cross", 1, 0.92) is True
    # If an attacker submits a forged token generated using JWT SECRET_KEY, it must be rejected:
    assert verify_approval_token(forged_token, "case_test_cross", 1, 0.92) is False


def test_approval_secret_cannot_validate_jwt_token():
    """A JWT token signed with SECRET_KEY cannot be decoded/validated using APPROVAL_TOKEN_SECRET."""
    token = create_access_token("user_123", "test_user", RoleEnum.CITIZEN)

    approval_secret = os.getenv("APPROVAL_TOKEN_SECRET")
    assert approval_secret is not None
    assert approval_secret != settings.SECRET_KEY

    # Validating with APPROVAL_TOKEN_SECRET must fail with InvalidSignatureError
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, approval_secret, algorithms=["HS256"])


def test_checkpoint_key_cannot_validate_approval_token():
    """An approval token cannot be verified with AUDIT_CHECKPOINT_KEY."""
    token = generate_approval_token("case_chk_cross", 1, 0.88)
    chk_key = os.getenv("AUDIT_CHECKPOINT_KEY") or getattr(settings, "AUDIT_CHECKPOINT_KEY", None)
    assert chk_key is not None

    import hashlib, hmac
    checkpoint_forged = hmac.new(
        chk_key.encode("utf-8"),
        f"case_chk_cross:1:0.8800".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    assert token != checkpoint_forged
    assert verify_approval_token(checkpoint_forged, "case_chk_cross", 1, 0.88) is False


def test_checkpoint_signature_uses_only_checkpoint_key():
    """Audit checkpoints strictly require AUDIT_CHECKPOINT_KEY and reject other keys."""
    chk_key = "audit-key-test-must-be-min-32-chars-long-123456"
    ledger = AuditLogLedger()
    chk = ledger.create_signed_checkpoint(secret_key=chk_key)

    # 1. Correct key verifies successfully
    res_valid = ledger.verify_checkpoint(chk, secret_key=chk_key)
    assert res_valid["is_valid"] is True

    # 2. JWT key fails signature verification
    res_jwt = ledger.verify_checkpoint(chk, secret_key=settings.SECRET_KEY)
    assert res_jwt["is_valid"] is False
    assert res_jwt["reason"] == "CHECKPOINT_SIGNATURE_INVALID"

    # 3. Approval token key fails signature verification
    approval_sec = os.getenv("APPROVAL_TOKEN_SECRET")
    res_app = ledger.verify_checkpoint(chk, secret_key=approval_sec)
    assert res_app["is_valid"] is False
    assert res_app["reason"] == "CHECKPOINT_SIGNATURE_INVALID"


def test_checkpoint_key_rotation_rejects_old_key():
    """Rotating AUDIT_CHECKPOINT_KEY rejects checkpoints created with the old key."""
    old_key = "audit-old-key-must-be-min-32-chars-long-aaaaaa"
    new_key = "audit-new-key-must-be-min-32-chars-long-bbbbbb"

    ledger = AuditLogLedger()
    chk_old = ledger.create_signed_checkpoint(secret_key=old_key)

    # Verification with new rotated key detects signature mismatch
    res = ledger.verify_checkpoint(chk_old, secret_key=new_key)
    assert res["is_valid"] is False
    assert res["reason"] == "CHECKPOINT_SIGNATURE_INVALID"


def test_settings_validation_rejects_identical_keys():
    """Settings model_validator must reject configurations where keys are identical."""
    shared_key = "shared-secret-that-violates-separation-min32"
    with pytest.raises(ValueError) as excinfo:
        Settings(
            SECRET_KEY=shared_key,
            APPROVAL_TOKEN_SECRET=shared_key,
            AUDIT_CHECKPOINT_KEY="distinct-audit-key-for-test-validation-32chars"
        )
    assert "Cryptographic key separation violation" in str(excinfo.value)


# ==============================================================================
# 2. TASK 2: CONSENT ENFORCEMENT & EXPLICIT DOCUMENTS SCOPE TESTS
# ==============================================================================

def test_case_creation_does_not_grant_documents_consent(client: TestClient, citizen_headers: dict):
    """Case creation alone must NOT grant DOCUMENTS consent."""
    case_payload = {
        "citizen_name": "Consent Test Citizen",
        "cnic": "42101-7766554-1",
        "phone": "0300-7654321",
        "household_size": 3,
        "monthly_income": 20000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 10000.0
    }
    res = client.post("/api/v1/cases", json=case_payload, headers=citizen_headers)
    assert res.status_code == 201
    cit_id = res.json()["citizen_id"]

    # Verify DOCUMENTS consent is NOT granted
    has_doc_consent = consent_gateway.check_consent(cit_id, ConsentScope.DOCUMENTS)
    assert has_doc_consent is False, "DOCUMENTS consent must NOT be auto-granted upon case creation"

    # Baseline IDENTITY and INCOME should be granted for case processing
    assert consent_gateway.check_consent(cit_id, ConsentScope.IDENTITY) is True
    assert consent_gateway.check_consent(cit_id, ConsentScope.INCOME) is True


def test_document_upload_fails_without_documents_consent(client: TestClient, citizen_headers: dict):
    """Attaching a document without explicit DOCUMENTS consent fails closed (403)."""
    case_payload = {
        "citizen_name": "No Doc Consent Citizen",
        "cnic": "42101-9988112-3",
        "phone": "0300-9988112",
        "household_size": 2,
        "monthly_income": 19000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 8000.0
    }
    case_res = client.post("/api/v1/cases", json=case_payload, headers=citizen_headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    doc_payload = {
        "doc_id": "doc_unauth_001",
        "doc_type": "cnic_front",
        "file_name": "cnic.jpg",
        "file_url": "https://storage.local/cnic.jpg",
        "ocr_confidence": 0.95,
        "is_blurry": False,
        "is_tampered": False
    }

    # Upload must be rejected with 403
    upload_res = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=citizen_headers)
    assert upload_res.status_code == 403
    assert upload_res.json()["detail"]["code"] == "CONSENT_WITHDRAWN"


def test_document_upload_succeeds_after_explicit_consent_and_fails_after_withdrawal(
    client: TestClient, citizen_headers: dict
):
    """Full lifecycle: upload fails -> explicit grant -> upload succeeds -> withdrawal -> upload fails."""
    case_payload = {
        "citizen_name": "Lifecycle Consent Citizen",
        "cnic": "42101-5544998-7",
        "phone": "0300-5544998",
        "household_size": 4,
        "monthly_income": 22000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 10000.0
    }
    case_res = client.post("/api/v1/cases", json=case_payload, headers=citizen_headers)
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]
    cit_id = case_res.json()["citizen_id"]

    doc_payload_1 = {
        "doc_id": "doc_lc_001",
        "doc_type": "cnic_front",
        "file_name": "cnic.jpg",
        "file_url": "https://storage.local/cnic.jpg",
        "ocr_confidence": 0.95,
        "is_blurry": False,
        "is_tampered": False
    }

    # 1. Without consent: 403
    r1 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload_1, headers=citizen_headers)
    assert r1.status_code == 403

    # 2. Explicit authenticated citizen action: grant DOCUMENTS consent
    grant_res = client.post("/api/v1/consent/grant", json={
        "citizen_id": cit_id,
        "scope": "documents"
    }, headers=citizen_headers)
    assert grant_res.status_code == 200
    assert grant_res.json()["granted"] is True

    # 3. With consent: 200 OK
    r2 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload_1, headers=citizen_headers)
    assert r2.status_code == 200
    assert len(r2.json()["documents"]) == 1

    # 4. Explicit withdrawal of DOCUMENTS consent
    withdraw_res = client.post("/api/v1/consent/withdraw", json={
        "citizen_id": cit_id,
        "scope": "documents"
    }, headers=citizen_headers)
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["granted"] is False

    # 5. Subsequent upload blocked: 403 Forbidden
    doc_payload_2 = dict(doc_payload_1, doc_id="doc_lc_002")
    r3 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload_2, headers=citizen_headers)
    assert r3.status_code == 403


def test_helper_and_officer_cannot_upload_without_citizen_documents_consent(
    client: TestClient, helper_headers: dict, officer_headers: dict
):
    """Helpers and Officers cannot attach documents to a case without the citizen's active DOCUMENTS consent."""
    from services.api.security.auth import _USERS_BY_USERNAME
    cit_id = _USERS_BY_USERNAME["citizen_parveen"]
    helper_id = _USERS_BY_USERNAME["helper_shazia"]

    # Ensure DOCUMENTS consent is NOT granted for citizen_parveen
    consent_gateway.withdraw_consent(cit_id, ConsentScope.DOCUMENTS, actor_id=cit_id, actor_role=RoleEnum.CITIZEN)

    # Create draft case directly
    from services.api.routes.cases import _CASES_DB
    from services.shared.schemas import CaseResponse, CaseStatus
    from datetime import datetime

    case_id = f"cas_unauth_test_{uuid.uuid4().hex[:6]}"
    _CASES_DB[case_id] = CaseResponse(
        id=case_id,
        citizen_id=cit_id,
        citizen_name="Parveen Bibi",
        cnic="42101-1234567-1",
        phone="0300-1234567",
        household_size=4,
        monthly_income=22000.0,
        benefit_type="relief_cash_grant",
        requested_amount=12000.0,
        status=CaseStatus.DRAFT,
        helper_id=helper_id,
        documents=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    doc_payload = {
        "doc_id": "doc_test_unauth",
        "doc_type": "utility_bill",
        "file_name": "bill.jpg",
        "file_url": "https://storage.local/bill.jpg",
        "ocr_confidence": 0.90,
        "is_blurry": False,
        "is_tampered": False
    }

    # Helper attempt -> 403
    res_helper = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=helper_headers)
    assert res_helper.status_code == 403

    # Officer attempt -> 403
    res_officer = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=officer_headers)
    assert res_officer.status_code == 403


# ==============================================================================
# 3. TASK 4: AUDIT LEDGER CLEAN ISOLATION & CONCURRENCY TESTS
# ==============================================================================

def test_clean_database_audit_chain_is_100_percent_valid():
    """Verifies that the isolated test database has a 100% valid, unbroken cryptographic hash chain."""
    res = audit_log.verify_chain(from_db=True)
    assert res.is_valid is True, f"Audit chain corrupted at index {res.corrupted_at_index}"
    assert res.corrupted_at_index is None
    assert res.head_hash is not None


def test_concurrent_audit_appends_preserve_unbroken_chain():
    """
    Simulates concurrent worker threads appending audit entries simultaneously.
    Verifies that thread-safe serialization guarantees zero broken prev_hash links.
    """
    ledger = AuditLogLedger()
    errors = []

    def worker(worker_id: str, count: int):
        for i in range(count):
            try:
                ledger.append(
                    actor_id=f"worker_{worker_id}",
                    actor_role=RoleEnum.OFFICER,
                    action=f"THREAD_ACTION_{worker_id}_{i}",
                    resource_id=f"res_{worker_id}",
                    details={"worker": worker_id, "iteration": i}
                )
            except Exception as e:
                errors.append(str(e))

    threads = [
        threading.Thread(target=worker, args=(f"T{t}", 5))
        for t in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent appends produced errors: {errors}"

    # Verify that the entire chain remains 100% mathematically valid
    chain_check = ledger.verify_chain(from_db=True)
    assert chain_check.is_valid is True, (
        f"Concurrent appends corrupted chain at index {chain_check.corrupted_at_index}!"
    )
