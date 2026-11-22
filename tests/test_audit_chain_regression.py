"""
Comprehensive Regression Test Suite for Audit Hash-Chain Integrity.
Tests:
- Actor IDs with colons and without (colon-splitting bug fix)
- Microsecond == 0 timestamps
- Complex details (nested, unicode, numeric)
- Full write-then-verify round trip through AuditLogLedger
- Fork prevention and stale in-memory entries list synchronization
- Repair tool unit test (dry run rollback, guard checks, and real commit)
"""
import uuid
from datetime import datetime

import pytest

from db.models import AuditLog as DBAuditLog
from db.models import Base
from services.api.engine.audit_log import (
    AuditLogLedger,
    calculate_hash,
)
from services.api.maintenance.repair_audit_chain import repair_chain
from services.shared.schemas import RoleEnum


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database has fresh tables for each test."""
    from db.connection import SessionLocal, engine
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        session.query(DBAuditLog).delete()
        session.commit()
    yield
    with SessionLocal() as session:
        session.query(DBAuditLog).delete()
        session.commit()


def test_actor_ids_with_colons_and_without():
    """Verifies that actor_ids containing single or multiple colons parse and verify correctly."""
    ledger = AuditLogLedger()

    # Variety of actor IDs with and without colons
    test_cases = [
        ("usr_normal", RoleEnum.CITIZEN, "ACTION_NORMAL"),
        ("helper:shazia", RoleEnum.HELPER, "ACTION_ONE_COLON"),
        ("api_key:demo:key_999", RoleEnum.ADMIN, "ACTION_TWO_COLONS"),
        ("service:worker:sub:proc_1", RoleEnum.OFFICER, "ACTION_THREE_COLONS"),
        ("system", RoleEnum.ADMIN, "ACTION_SYSTEM"),
    ]

    for actor_id, role, action in test_cases:
        entry = ledger.append(
            actor_id=actor_id,
            actor_role=role,
            action=action,
            resource_id="res_test",
            details={"actor_tested": actor_id}
        )
        assert entry.current_hash is not None

    # Authoritative DB verification
    res_db = ledger.verify_chain(from_db=True)
    assert res_db.is_valid is True, f"DB verification failed at index {res_db.corrupted_at_index}"

    # In-memory mirror verification
    res_mem = ledger.verify_chain(from_db=False)
    assert res_mem.is_valid is True, f"Memory verification failed at index {res_mem.corrupted_at_index}"


def test_timestamp_microsecond_zero():
    """Verifies that timestamps with microsecond == 0 round trip and verify without error."""
    from db.connection import SessionLocal

    ledger = AuditLogLedger()
    prev = ledger.latest_hash
    ts_zero = datetime(2026, 11, 21, 14, 30, 0, 0)  # microsecond is exactly 0
    assert ts_zero.microsecond == 0

    curr_h = calculate_hash(
        prev_hash=prev,
        timestamp=ts_zero.isoformat(),
        actor_id="helper:aslam",
        actor_role="helper",
        action="TEST_MICROSECOND_ZERO",
        resource_id="cit_zero_001",
        details={"status": "zero_microsecond"}
    )

    with SessionLocal() as session:
        row = DBAuditLog(
            prev_hash=prev,
            current_hash=curr_h,
            actor="helper:aslam:helper",
            action="TEST_MICROSECOND_ZERO",
            target="cit_zero_001",
            result="SUCCESS",
            request_id="aud_zero_001",
            timestamp=ts_zero,
            details={"status": "zero_microsecond"}
        )
        session.add(row)
        session.commit()

    res = ledger.verify_chain(from_db=True)
    assert res.is_valid is True, f"Failed for microsecond==0 at index {res.corrupted_at_index}"


def test_details_nested_unicode_and_numbers():
    """Verifies that complex details payloads (nested dicts, unicode Urdu, floats, ints) verify cleanly."""
    ledger = AuditLogLedger()

    complex_details = {
        "urdu_text": "سیلاب متاثرین کے لیے ایمرجنسی کیش گرانٹ",
        "family": {
            "head": "پروین بی بی",
            "dependents": [
                {"name": "علی", "age": 10, "cnic": "42101-1111111-1"},
                {"name": "زینب", "age": 7, "cnic": None}
            ]
        },
        "metrics": {
            "requested_amount": 25000.75,
            "approved_amount": 25000,
            "confidence_score": 0.987654,
            "is_emergency": True
        }
    }

    entry = ledger.append(
        actor_id="officer:ahmed:field",
        actor_role=RoleEnum.OFFICER,
        action="COMPLEX_DETAILS_LOGGED",
        resource_id="case_complex_001",
        details=complex_details
    )

    assert entry.current_hash is not None
    res = ledger.verify_chain(from_db=True)
    assert res.is_valid is True, f"Failed on complex details: {res}"


def test_write_then_verify_round_trip():
    """Verifies write-then-read verification across 10 sequential ledger appends."""
    ledger = AuditLogLedger()

    for i in range(10):
        ledger.append(
            actor_id=f"user:{i}:citizen",
            actor_role=RoleEnum.CITIZEN,
            action=f"CITIZEN_STEP_{i}",
            resource_id=f"res_{i}",
            details={"iteration": i, "token": uuid.uuid4().hex}
        )

    res = ledger.verify_chain(from_db=True)
    assert res.is_valid is True
    assert res.total_records >= 10
    assert res.corrupted_at_index is None


def test_fork_prevention_and_stale_in_memory_sync():
    """
    Simulates a stale in-memory entries list and verifies that append()
    always queries the database for latest_db to guarantee prev_hash matches latest DB hash.
    """
    from db.connection import SessionLocal

    ledger_instance_1 = AuditLogLedger()
    e1 = ledger_instance_1.append("usr_1", RoleEnum.CITIZEN, "ACTION_1", "res_1")

    # Simulate an external writer committing an entry directly to DB (so ledger_instance_1 has stale _entries)
    with SessionLocal() as session:
        external_ts = datetime.utcnow()
        external_h = calculate_hash(
            prev_hash=e1.current_hash,
            timestamp=external_ts.isoformat(),
            actor_id="external:writer",
            actor_role="admin",
            action="EXTERNAL_ACTION",
            resource_id="res_ext",
            details={"source": "external_worker"}
        )
        ext_entry = DBAuditLog(
            prev_hash=e1.current_hash,
            current_hash=external_h,
            actor="external:writer:admin",
            action="EXTERNAL_ACTION",
            target="res_ext",
            result="SUCCESS",
            request_id="aud_ext_001",
            timestamp=external_ts,
            details={"source": "external_worker"}
        )
        session.add(ext_entry)
        session.commit()

    # Now ledger_instance_1's in-memory _entries ends at e1, but DB ends at ext_entry
    assert ledger_instance_1._entries[-1].current_hash != external_h

    # Appending on ledger_instance_1 MUST read latest DB hash as prev_hash (not stale in-memory)
    e3 = ledger_instance_1.append("usr_3", RoleEnum.OFFICER, "ACTION_3", "res_3")

    # Prev hash of e3 MUST equal the external entry's hash (no fork!)
    assert e3.prev_hash == external_h
    # In-memory entries must have re-synced from DB
    assert ledger_instance_1._entries[-1].current_hash == e3.current_hash

    # Whole chain must be strictly valid
    res = ledger_instance_1.verify_chain(from_db=True)
    assert res.is_valid is True
    assert res.corrupted_at_index is None


def test_repair_tool_dry_run_and_commit(monkeypatch):
    """
    Tests repair_audit_chain:
    1. Sets up broken rows (fork + corrupted hash).
    2. Runs dry-run: verifies rollback leaves chain broken.
    3. Runs with wrong expected id: aborts.
    4. Runs real commit: repairs chain, adds AUDIT_CHAIN_REPAIRED, leaves earlier rows untouched.
    """
    from db.connection import SessionLocal

    ledger = AuditLogLedger()
    # Create 3 valid entries
    ledger.append("admin:root", RoleEnum.ADMIN, "STEP_1", "res_1")
    ledger.append("officer:aslam", RoleEnum.OFFICER, "STEP_2", "res_2")
    e3 = ledger.append("helper:shazia", RoleEnum.HELPER, "STEP_3", "res_3")

    valid_head_hash = e3.current_hash

    # Create intentional corruption in DB starting at row 4
    with SessionLocal() as session:
        # Row 4: corrupted prev_hash (fork / link break)
        broken_ts_4 = datetime.utcnow()
        row_4_h = calculate_hash("bad_prev_hash", broken_ts_4.isoformat(), "helper:shazia", "helper", "CORRUPTED_STEP_4", "res_4", {})
        r4 = DBAuditLog(
            prev_hash="bad_prev_hash",
            current_hash=row_4_h,
            actor="helper:shazia:helper",
            action="CORRUPTED_STEP_4",
            target="res_4",
            result="SUCCESS",
            request_id="aud_corrupt_4",
            timestamp=broken_ts_4,
            details={"step": 4}
        )
        session.add(r4)
        session.flush()
        first_broken_id = r4.id

        # Row 5: linked to row 4
        broken_ts_5 = datetime.utcnow()
        row_5_h = calculate_hash(row_4_h, broken_ts_5.isoformat(), "citizen:parveen", "citizen", "CORRUPTED_STEP_5", "res_5", {})
        r5 = DBAuditLog(
            prev_hash=row_4_h,
            current_hash=row_5_h,
            actor="citizen:parveen:citizen",
            action="CORRUPTED_STEP_5",
            target="res_5",
            result="SUCCESS",
            request_id="aud_corrupt_5",
            timestamp=broken_ts_5,
            details={"step": 5}
        )
        session.add(r5)
        session.commit()

    # Verification must fail before repair
    res_before = ledger.verify_chain(from_db=True)
    assert res_before.is_valid is False
    assert res_before.corrupted_at_index is not None

    # --- Test 1: Dry Run Mode (Default) ---
    monkeypatch.delenv("REPAIR_APPLY", raising=False)
    monkeypatch.delenv("REPAIR_EXPECT_FIRST_ID", raising=False)
    code_dry = repair_chain()
    assert code_dry == 0
    # Because dry run rolls back, chain is still broken
    assert ledger.verify_chain(from_db=True).is_valid is False

    # --- Test 2: Apply with Mismatched Expected ID -> Aborts ---
    monkeypatch.setenv("REPAIR_APPLY", "1")
    monkeypatch.setenv("REPAIR_EXPECT_FIRST_ID", str(first_broken_id + 999))
    code_mismatch = repair_chain()
    assert code_mismatch != 0
    # Still broken
    assert ledger.verify_chain(from_db=True).is_valid is False

    # --- Test 3: Real Commit with Correct Expected ID ---
    monkeypatch.setenv("REPAIR_APPLY", "1")
    monkeypatch.setenv("REPAIR_EXPECT_FIRST_ID", str(first_broken_id))
    code_apply = repair_chain()
    assert code_apply == 0

    # Chain must now be completely valid!
    res_after = ledger.verify_chain(from_db=True)
    assert res_after.is_valid is True
    assert res_after.corrupted_at_index is None

    # Check rows before first_broken_id were UNTOUCHED
    with SessionLocal() as session:
        untouched_row_3 = session.query(DBAuditLog).filter_by(action="STEP_3").first()
        assert untouched_row_3.current_hash == valid_head_hash

        # Check AUDIT_CHAIN_REPAIRED row was appended
        repair_row = session.query(DBAuditLog).filter_by(action="AUDIT_CHAIN_REPAIRED").first()
        assert repair_row is not None
        assert repair_row.actor == "system:admin"
        assert repair_row.details["first_row_id"] == first_broken_id
        assert repair_row.details["rows_rewritten"] == 2
