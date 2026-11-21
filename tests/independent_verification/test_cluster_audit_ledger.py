"""
Comprehensive Test Suite for Cluster-Safe, Database-Backed Audit Ledger.
Task 2 Verification:
- Two workers appending audit records concurrently
- Strict single unbroken cryptographic chain in PostgreSQL
- Historical record modification detection in PostgreSQL
- Historical record deletion detection in PostgreSQL
- Application restart persistence
- Fail-closed behavior on database outage (no silent data loss)
- Concurrency serialization via PostgreSQL transaction advisory lock
"""
import threading
from unittest.mock import patch

import pytest

from db.connection import SessionLocal
from db.models import AuditLog as DBAuditLog
from services.api.engine.audit_log import AuditLogLedger
from services.shared.schemas import RoleEnum


def test_concurrent_worker_appends_single_valid_chain():
    """Verifies that 2 concurrent worker threads produce a single, unbroken chain in PostgreSQL."""
    results = {}

    def worker_thread(worker_name: str, count: int):
        try:
            ledger = AuditLogLedger()
            ids = []
            for i in range(count):
                e = ledger.append(
                    actor_id=f"worker_{worker_name}",
                    actor_role=RoleEnum.OFFICER,
                    action=f"CONCURRENT_ACTION_{worker_name}_{i}",
                    resource_id=f"RES_{worker_name}_{i}",
                    details={"worker": worker_name, "seq": i}
                )
                ids.append(e.id)
            results[worker_name] = {"success": True, "ids": ids}
        except Exception as e:
            results[worker_name] = {"success": False, "error": str(e)}

    t1 = threading.Thread(target=worker_thread, args=("alpha_t", 4))
    t2 = threading.Thread(target=worker_thread, args=("beta_t", 4))

    t1.start()
    t2.start()

    t1.join(timeout=20)
    t2.join(timeout=20)

    assert results.get("alpha_t", {}).get("success") is True, f"Worker Alpha failed: {results.get('alpha_t')}"
    assert results.get("beta_t", {}).get("success") is True, f"Worker Beta failed: {results.get('beta_t')}"

    # Verify that the entire database ledger is valid from Genesis to Head
    ledger = AuditLogLedger()
    res = ledger.verify_chain()
    assert res.is_valid is True, f"Audit chain verification failed: corrupted at index {res.corrupted_at_index}"
    assert res.corrupted_at_index is None
    assert res.total_records >= 9


def test_historical_record_modification_detected():
    """Modifying any historical field in PostgreSQL must immediately trigger tamper detection."""
    ledger = AuditLogLedger()
    target_entry = ledger.append("auditor_test", RoleEnum.AUDITOR, "TAMPER_CHECK_ACTION", "TARGET_TAMPER_01", {"val": 100})

    # Verify valid before tampering
    assert ledger.verify_chain().is_valid is True

    # Tamper with the row directly in PostgreSQL
    with SessionLocal() as db_session:
        db_row = db_session.query(DBAuditLog).filter_by(request_id=target_entry.id).first()
        assert db_row is not None
        original_action = db_row.action
        db_row.action = "FORGED_MALICIOUS_ACTION"
        db_session.commit()

    try:
        # verify_chain() must detect the tamper in PostgreSQL
        verification = ledger.verify_chain()
        assert verification.is_valid is False
        assert verification.corrupted_at_index is not None
    finally:
        # Restore row
        with SessionLocal() as db_session:
            db_row = db_session.query(DBAuditLog).filter_by(request_id=target_entry.id).first()
            if db_row:
                db_row.action = original_action
                db_session.commit()


def test_historical_record_deletion_detected():
    """Deleting a record creates a cryptographic break and must be detected immediately."""
    ledger = AuditLogLedger()
    ledger.append("admin", RoleEnum.ADMIN, "RECORD_A", "RES_A", {"seq": 1})
    e2 = ledger.append("admin", RoleEnum.ADMIN, "RECORD_B", "RES_B", {"seq": 2})
    ledger.append("admin", RoleEnum.ADMIN, "RECORD_C", "RES_C", {"seq": 3})

    assert ledger.verify_chain().is_valid is True

    # Delete e2 from database
    with SessionLocal() as db_session:
        deleted_row = db_session.query(DBAuditLog).filter_by(request_id=e2.id).first()
        saved_dict = {
            "id": deleted_row.id,
            "prev_hash": deleted_row.prev_hash,
            "current_hash": deleted_row.current_hash,
            "actor": deleted_row.actor,
            "action": deleted_row.action,
            "target": deleted_row.target,
            "result": deleted_row.result,
            "request_id": deleted_row.request_id,
            "timestamp": deleted_row.timestamp,
            "details": deleted_row.details
        }
        db_session.delete(deleted_row)
        db_session.commit()

    try:
        # With e2 deleted, e3.prev_hash no longer matches e1.current_hash
        res = ledger.verify_chain()
        assert res.is_valid is False
        assert res.corrupted_at_index is not None
    finally:
        # Restore row
        with SessionLocal() as db_session:
            restored = DBAuditLog(**saved_dict)
            db_session.add(restored)
            db_session.commit()


def test_application_restart_persistence():
    """Creating a brand new AuditLogLedger instance simulates app restart and verifies chain from DB."""
    ledger_instance_1 = AuditLogLedger()
    ledger_instance_1.append("worker_x", RoleEnum.OFFICER, "PRE_RESTART_ACTION", "SYS_01")

    # Simulate restart: delete in-memory instance, create fresh instance
    del ledger_instance_1

    fresh_ledger = AuditLogLedger()
    res = fresh_ledger.verify_chain()
    assert res.is_valid is True
    assert res.total_records > 0
    assert res.head_hash == fresh_ledger.latest_hash


def test_database_outage_fails_closed():
    """When PostgreSQL is unreachable, append() must raise an exception rather than silently losing logs."""
    ledger = AuditLogLedger()

    # Simulate database connection outage
    with patch("db.connection.SessionLocal", side_effect=Exception("Connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            ledger.append("worker_y", RoleEnum.ADMIN, "CRITICAL_SECURITY_EVENT", "RES_FAIL")

        assert "Audit log persistence failure" in str(exc_info.value)
        assert "database unavailable" in str(exc_info.value)
