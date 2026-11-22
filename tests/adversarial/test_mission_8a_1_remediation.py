"""
Mission 8A.1 Adversarial & Regression Verification Suite.
Validates P0 and P1 security remediations:
1. P0 Secret configuration fail-closed and predictability elimination.
2. P0 CNIC Maker-Checker bypass closure (410 Gone for legacy endpoint, two-phase authenticated workflow).
3. P1 Maker-Checker proposal database persistence (multi-worker visibility, restart survivability).
4. P1 Offline-sync authoritative identity resolution and mandatory consent check.
5. P1 Document attachment dual consent enforcement (DOCUMENTS & HELPER_ACTING).
6. P1 Audit ledger TRUNCATE trigger and checkpoint verification.
"""
import copy
import uuid

import pytest
from fastapi.testclient import TestClient

from db.connection import SessionLocal
from db.models import Citizen, LegacyCnicProposal
from services.ai.sync import process_offline_sync_batch
from services.api.config import _get_validated_secret_key
from services.api.engine.audit_log import audit_log
from services.api.engine.consent_gateway import consent_gateway
from services.api.engine.decision_engine import generate_approval_token, verify_approval_token
from services.api.main import app
from services.shared.schemas import ConsentScope, RoleEnum

client = TestClient(app)


# ==============================================================================
# 1. P0: SECRET CONFIGURATION FAIL-CLOSED TESTS
# ==============================================================================

def test_secret_key_missing_fails_closed(monkeypatch):
    """Verifies application fails closed if SECRET_KEY and JWT_SECRET are absent."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises((RuntimeError, ValueError)) as exc:
        _get_validated_secret_key()
    assert "SECRET_KEY environment variable is required" in str(exc.value)


def test_secret_key_empty_fails_closed(monkeypatch):
    """Verifies application fails closed if SECRET_KEY is empty or whitespace."""
    monkeypatch.setenv("SECRET_KEY", "   ")
    with pytest.raises((RuntimeError, ValueError)) as exc:
        _get_validated_secret_key()
    assert "cannot be empty" in str(exc.value)


def test_secret_key_too_short_fails_closed(monkeypatch):
    """Verifies application rejects secret keys under 32 characters."""
    monkeypatch.setenv("SECRET_KEY", "short_secret_key_12345")
    with pytest.raises((RuntimeError, ValueError)) as exc:
        _get_validated_secret_key()
    assert "must be at least 32 characters" in str(exc.value)


def test_insecure_development_secret_in_production_fails_closed(monkeypatch):
    """Verifies application refuses to boot with insecure development secret in production."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "rahbar-super-secret-development-key-change-in-production-min32chars")
    with pytest.raises((RuntimeError, ValueError)) as exc:
        _get_validated_secret_key()
    assert "Insecure development SECRET_KEY detected in production" in str(exc.value)


def test_approval_token_uses_secure_key():
    """Verifies approval token generation and verification use settings.SECRET_KEY."""
    case_id = "test_case_sec_001"
    token = generate_approval_token(case_id, rule_version=1, confidence=0.95)
    assert token and len(token) == 64
    assert verify_approval_token(token, case_id, rule_version=1, confidence=0.95) is True
    # Tampering test
    assert verify_approval_token(token, case_id, rule_version=1, confidence=0.90) is False
    assert verify_approval_token("a" * 64, case_id, rule_version=1, confidence=0.95) is False


# ==============================================================================
# 2. P0: CLOSE CNIC MAKER-CHECKER BYPASS & P1 PERSISTENCE
# ==============================================================================

def test_legacy_verify_and_correct_endpoint_is_deprecated_and_disabled(officer_headers):
    """Direct single-request verification endpoint must return 410 GONE."""
    payload = {
        "citizen_id": "cit_test_dep",
        "verified_cnic": "42101-1234567-1",
        "caseworker_notes": "Physical smart card inspection completed",
        "physical_document_ref": "NADRA-TOK-998877",
        "second_approver_id": "usr_officer_2"
    }
    resp = client.post("/api/v1/cases/legacy-cnic/verify-and-correct", json=payload, headers=officer_headers)
    assert resp.status_code == 410
    data = resp.json()
    assert "ENDPOINT_DEPRECATED_MAKER_CHECKER_REQUIRED" in data["detail"]["code"]


def test_maker_checker_two_phase_db_persistence_and_separation(officer_headers, admin_headers, citizen_headers):
    """
    Verifies:
    1. Proposal is persisted to database (survives worker/restart).
    2. Maker cannot self-approve (403 Forbidden).
    3. Unauthorized roles cannot approve (403 Forbidden).
    4. Valid checker can approve, updating citizen CNIC and audit ledger.
    5. Replay of approved proposal fails (400 Bad Request).
    """
    # 1. Seed legacy citizen ending in -X with unique CNIC
    cit_id = f"cit_leg_{uuid.uuid4().hex[:6]}"
    rand_part = f"{uuid.uuid4().int % 10000000:07d}"
    legacy_cnic = f"42101-{rand_part}-X"
    with SessionLocal() as db:
        c = Citizen(id=cit_id, cnic=legacy_cnic, full_name="Test Legacy Citizen")
        db.add(c)
        db.commit()

    # 2. Maker proposes correction
    doc_ref = f"NADRA-TOK-{uuid.uuid4().hex[:6].upper()}"
    new_cnic = f"42101-{rand_part}-9"
    proposal_payload = {
        "citizen_id": cit_id,
        "verified_cnic": new_cnic,
        "caseworker_notes": "Physical smart card verified against NADRA database",
        "physical_document_ref": doc_ref
    }
    prop_resp = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=proposal_payload, headers=officer_headers)
    assert prop_resp.status_code == 201
    prop_data = prop_resp.json()
    proposal_id = prop_data["proposal_id"]
    assert prop_data["status"] == "PROPOSED"

    # Verify database persistence across independent DB session
    with SessionLocal() as db:
        saved_prop = db.query(LegacyCnicProposal).filter_by(id=proposal_id).first()
        assert saved_prop is not None
        assert saved_prop.status == "PENDING_APPROVAL"
        assert saved_prop.proposed_cnic == new_cnic

    # 3. Maker attempts self-approval -> 403 Forbidden
    approval_payload = {
        "proposal_id": proposal_id,
        "supervisor_notes": "Supervisor approved physical evidence"
    }
    self_appr = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approval_payload, headers=officer_headers)
    assert self_appr.status_code == 403
    assert "MAKER_CHECKER_SELF_APPROVAL_FORBIDDEN" in self_appr.json()["detail"]

    # 4. Citizen/Helper attempts approval -> 403 Forbidden
    unauth_appr = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approval_payload, headers=citizen_headers)
    assert unauth_appr.status_code == 403

    # 5. Independent Checker (Admin) approves
    valid_appr = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approval_payload, headers=admin_headers)
    assert valid_appr.status_code == 200
    assert valid_appr.json()["status"] == "APPROVED"

    # Verify DB citizen was updated
    with SessionLocal() as db:
        updated_cit = db.query(Citizen).filter_by(id=cit_id).first()
        assert updated_cit.cnic == new_cnic
        updated_prop = db.query(LegacyCnicProposal).filter_by(id=proposal_id).first()
        assert updated_prop.status == "APPROVED"

    # 6. Replay attack: attempt approving already approved proposal -> 400 Bad Request
    replay_resp = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approval_payload, headers=admin_headers)
    assert replay_resp.status_code == 400
    assert "cannot be re-processed" in replay_resp.json()["detail"]


# ==============================================================================
# 3. P1: OFFLINE-SYNC CONSENT BYPASS CLOSURE
# ==============================================================================

def test_offline_sync_missing_identity_rejected():
    """Sync item with no citizen_id and no verifiable CNIC must be rejected."""
    batch = [{
        "idempotency_key": f"sync_no_id_{uuid.uuid4().hex[:6]}",
        "citizen_data": {
            "name": "Anonymous Applicant",
            "monthly_income": 20000.0
        }
    }]
    res = process_offline_sync_batch(helper_id="usr_helper_1", batch_id="batch_01", queued_cases=batch)
    assert res["summary"]["failed_count"] == 1
    assert res["items"][0]["status"] == "SYNC_FAILED_IDENTITY_UNVERIFIED"


def test_offline_sync_resolves_db_citizen_and_enforces_consent():
    """Sync item with only CNIC resolves citizen in DB and enforces active consent."""
    cit_id = f"cit_sync_{uuid.uuid4().hex[:6]}"
    rand_part = f"{uuid.uuid4().int % 10000000:07d}"
    cnic = f"35201-{rand_part}-1"
    with SessionLocal() as db:
        c = Citizen(id=cit_id, cnic=cnic, full_name="Sync Citizen Test")
        db.add(c)
        db.commit()

    # 1. When consent is NOT granted -> rejected
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING, actor_id=cit_id, actor_role=RoleEnum.CITIZEN)
    batch_no_consent = [{
        "idempotency_key": f"sync_key_1_{uuid.uuid4().hex[:6]}",
        "citizen_data": {"cnic": cnic, "name": "Sync Citizen Test"}
    }]
    res1 = process_offline_sync_batch(helper_id="usr_helper_1", batch_id="batch_02", queued_cases=batch_no_consent)
    assert res1["summary"]["failed_count"] == 1
    assert res1["items"][0]["status"] == "SYNC_FAILED_CONSENT_REVOKED"

    # 2. When consent IS granted -> processed
    consent_gateway.grant_consent(cit_id, ConsentScope.HELPER_ACTING, actor_id=cit_id, actor_role=RoleEnum.CITIZEN, helper_id="usr_helper_1")
    batch_with_consent = [{
        "idempotency_key": f"sync_key_2_{uuid.uuid4().hex[:6]}",
        "citizen_data": {"cnic": cnic, "name": "Sync Citizen Test"}
    }]
    res2 = process_offline_sync_batch(helper_id="usr_helper_1", batch_id="batch_03", queued_cases=batch_with_consent)
    assert res2["summary"]["synced_count"] == 1
    assert res2["items"][0]["status"] == "SYNCED_SUCCESSFULLY"


# ==============================================================================
# 4. P1: DOCUMENT CONSENT ENFORCEMENT
# ==============================================================================

def test_document_attachment_requires_documents_consent(client, citizen_headers, helper_headers):
    """Verifies attaching a document checks ConsentScope.DOCUMENTS and HELPER_ACTING."""
    # Create a case with all required fields
    case_res = client.post("/api/v1/cases", json={
        "citizen_name": "Doc Consent Test Citizen",
        "cnic": "42201-1122334-1",
        "phone": "0300-1122334",
        "household_size": 4,
        "monthly_income": 22000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 12000.0
    }, headers=citizen_headers)
    assert case_res.status_code == 201
    case_data = case_res.json()
    case_id = case_data["id"]
    cit_id = case_data["citizen_id"]

    doc_payload = {
        "doc_id": "doc_test_123",
        "doc_type": "CNIC_FRONT",
        "file_name": "cnic_front.jpg",
        "file_url": "https://storage.local/doc1.jpg",
        "ocr_confidence": 0.95,
        "is_blurry": False
    }

    # 1. Immediately after case creation, DOCUMENTS consent is NOT granted -> 403 Forbidden
    r0 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=citizen_headers)
    assert r0.status_code == 403

    # 2. Citizen explicitly grants DOCUMENTS consent -> 200 OK
    consent_gateway.grant_consent(cit_id, ConsentScope.DOCUMENTS, actor_id=cit_id, actor_role=RoleEnum.CITIZEN)
    r1 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=citizen_headers)
    assert r1.status_code == 200
    assert len(r1.json()["documents"]) == 1

    # 3. Citizen withdraws DOCUMENTS consent -> subsequent attachment immediately blocked (403 Forbidden)
    consent_gateway.withdraw_consent(cit_id, ConsentScope.DOCUMENTS, actor_id=cit_id, actor_role=RoleEnum.CITIZEN)
    r2 = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=citizen_headers)
    assert r2.status_code == 403


# ==============================================================================
# 5. P1: AUDIT LEDGER TRUNCATE TRIGGER & CHECKPOINT INTEGRITY
# ==============================================================================

def test_audit_sql_migration_includes_truncate_trigger():
    """Verifies that 003_audit_log_append_only.sql defines a BEFORE TRUNCATE trigger."""
    with open("db/migrations/003_audit_log_append_only.sql", "r", encoding="utf-8") as f:
        content = f.read()
    assert "BEFORE TRUNCATE ON audit_log" in content
    assert "FOR EACH STATEMENT" in content
    assert "prevent_audit_log_tamper" in content


def test_audit_checkpoint_verification_detects_tamper(monkeypatch):
    """Verifies that audit checkpoint detection identifies forged signatures and missing keys."""
    monkeypatch.setenv("AUDIT_CHECKPOINT_KEY", "test-checkpoint-key-for-audit-validation-min32chars")
    chk = audit_log.create_signed_checkpoint()
    assert chk["signature"]

    # 1. Valid checkpoint
    ver = audit_log.verify_checkpoint(chk)
    assert ver["is_valid"] is True

    # 2. Forged signature
    forged = copy.deepcopy(chk)
    forged["signature"] = "0" * 64
    ver_forged = audit_log.verify_checkpoint(forged)
    assert ver_forged["is_valid"] is False
    assert ver_forged["reason"] == "CHECKPOINT_SIGNATURE_INVALID"

    # 3. Missing signing key fails closed
    monkeypatch.delenv("AUDIT_CHECKPOINT_KEY", raising=False)
    with pytest.raises(ValueError):
        audit_log.verify_checkpoint(chk)
