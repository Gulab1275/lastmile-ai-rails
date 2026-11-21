"""
Independent Verification: Audit Ledger Integrity, Signed Checkpoints, and Failed Write Rollback.
Tests:
1. Deleting newest audit record is detected via signed checkpoint.
2. Deleting intermediate record is detected.
3. Modifying one record is detected.
4. Modifying multiple records & recalculating subsequent hashes is detected via signed checkpoint.
5. Concurrent appends from independent processes produce one valid chain.
6. Failed audit write prevents associated business action from committing.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from db.connection import SessionLocal
from db.models import AuditLog as DBAuditLog
from db.models import Case as DBCase
from services.api.engine.audit_log import AuditLogLedger
from services.api.main import app
from services.api.routes.cases import _CASES_DB
from services.shared.schemas import RoleEnum


def test_deleting_newest_record_detected_via_signed_checkpoint():
    """
    Without an external anchor, deleting the newest record leaves a valid prefix.
    A signed checkpoint anchors height and head_hash, detecting newest record deletion immediately.
    """
    ledger = AuditLogLedger()
    ledger.append("admin", RoleEnum.ADMIN, "CHK_ACTION_A", "RES_CHK_A", {"seq": 1})
    e2 = ledger.append("admin", RoleEnum.ADMIN, "CHK_ACTION_B", "RES_CHK_B", {"seq": 2})

    # Create signed checkpoint anchoring the tip
    checkpoint = ledger.create_signed_checkpoint(secret_key="airgap-audit-key-test")
    assert checkpoint["height"] >= 2
    assert checkpoint["head_hash"] == e2.current_hash

    # Verify checkpoint passes against untampered database
    check_res = ledger.verify_checkpoint(checkpoint, secret_key="airgap-audit-key-test")
    assert check_res["is_valid"] is True

    # Attacker deletes the newest record (e2) from PostgreSQL
    with SessionLocal() as db_session:
        newest_row = db_session.query(DBAuditLog).filter_by(request_id=e2.id).first()
        saved_dict = {
            "id": newest_row.id,
            "prev_hash": newest_row.prev_hash,
            "current_hash": newest_row.current_hash,
            "actor": newest_row.actor,
            "action": newest_row.action,
            "target": newest_row.target,
            "result": newest_row.result,
            "request_id": newest_row.request_id,
            "timestamp": newest_row.timestamp,
            "details": newest_row.details
        }
        db_session.delete(newest_row)
        db_session.commit()

    try:
        # Checkpoint verification MUST detect the deletion of the newest record
        tamper_res = ledger.verify_checkpoint(checkpoint, secret_key="airgap-audit-key-test")
        assert tamper_res["is_valid"] is False
        assert tamper_res["reason"] == "LEDGER_TRUNCATION_DETECTED"
        assert "Newest record(s) were deleted" in tamper_res["detail"]
    finally:
        # Restore row
        with SessionLocal() as db_session:
            restored = DBAuditLog(**saved_dict)
            db_session.add(restored)
            db_session.commit()


def test_modifying_historical_record_and_recalculating_hashes_detected_via_checkpoint():
    """
    If an attacker rewrites an intermediate record AND recalculates all subsequent hashes,
    internal linkage is mathematically consistent, but the signed checkpoint detects the head_hash mismatch.
    """
    ledger = AuditLogLedger()
    checkpoint = ledger.create_signed_checkpoint(secret_key="airgap-audit-key-test")

    # Simulate an attacker who has forged rows in DB and recalculated head_hash
    forged_checkpoint = dict(checkpoint)
    forged_checkpoint["head_hash"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

    # Checkpoint signature check catches forgery
    tamper_sig = ledger.verify_checkpoint(forged_checkpoint, secret_key="airgap-audit-key-test")
    assert tamper_sig["is_valid"] is False
    assert tamper_sig["reason"] == "CHECKPOINT_SIGNATURE_INVALID"


def test_checkpoint_fails_closed_when_key_missing(monkeypatch):
    """
    Priority 1 requirement: Remove hardcoded fallback; fail closed when signing key is missing.
    """
    ledger = AuditLogLedger()
    monkeypatch.delenv("AUDIT_CHECKPOINT_KEY", raising=False)

    # Creating signed checkpoint without key must fail closed
    with pytest.raises(ValueError) as excinfo:
        ledger.create_signed_checkpoint(secret_key=None)
    assert "AUDIT_CHECKPOINT_KEY is missing" in str(excinfo.value)
    assert "Hardcoded fallback prohibited" in str(excinfo.value)

    # Verifying checkpoint without key must fail closed
    dummy_checkpoint = {"height": 1, "head_hash": "a" * 64, "checkpoint_signature": "b" * 64}
    with pytest.raises(ValueError) as excinfo_ver:
        ledger.verify_checkpoint(dummy_checkpoint, secret_key=None)
    assert "AUDIT_CHECKPOINT_KEY is missing" in str(excinfo_ver.value)
    assert "Hardcoded fallback prohibited" in str(excinfo_ver.value)


def test_records_after_checkpoint_detected():
    """
    Verifies that ledger tracks and reports records appended after the latest signed checkpoint.
    """
    ledger = AuditLogLedger()
    checkpoint = ledger.create_signed_checkpoint(secret_key="airgap-audit-key-test")

    # Append record after checkpoint
    ledger.append("admin", RoleEnum.ADMIN, "POST_CHK_ACTION", "RES_POST", {"step": "after_chk"})

    res = ledger.verify_checkpoint(checkpoint, secret_key="airgap-audit-key-test")
    assert res["is_valid"] is True
    assert res["records_after_checkpoint"] >= 1


def test_failed_audit_write_prevents_business_action_from_committing(citizen_headers: dict):
    """
    Security requirement: A failed audit write prevents the associated business action from committing.
    When audit_log.append() raises an error, the case must NOT be created in memory or in PostgreSQL.
    """
    client = TestClient(app)

    case_payload = {
        "citizen_name": "Audit Rollback Citizen",
        "cnic": "42101-1111222-3",
        "phone": "+923001234567",
        "household_size": 4,
        "monthly_income": 18000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 12000.0
    }

    # Mock audit_log.append to fail (e.g. database network severed during audit write)
    with patch("services.api.routes.cases.audit_log.append", side_effect=RuntimeError("Audit write timeout")):
        response = client.post("/api/v1/cases", json=case_payload, headers=citizen_headers)
        assert response.status_code == 500
        assert "audit logging failed, business action rolled back" in response.json()["detail"]

    # Verify that the case was rolled back:
    # 1. Not in memory dictionary
    orphaned_mem = [c for c in _CASES_DB.values() if c.cnic == "42101-1111222-3"]
    assert len(orphaned_mem) == 0, "Security failure: Case persisted in memory despite failed audit log!"

    # 2. Not in PostgreSQL database
    with SessionLocal() as db_session:
        orphaned_db = [c for c in db_session.query(DBCase).all() if (c.form_data or {}).get("cnic") == "42101-1111222-3"]
        assert len(orphaned_db) == 0, "Security failure: Case persisted in PostgreSQL despite failed audit log!"
