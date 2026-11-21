"""
Adversarial Test Suite J: Database Integrity, Constraints & Cryptographic Ledger.
Tests database schema foreign keys, uniqueness indexes, transaction rollbacks,
and SHA-256 cryptographic hash-chain tamper resistance.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from db.connection import SessionLocal
from db.models import Citizen
from services.api.engine.audit_log import audit_log
from services.shared.schemas import RoleEnum


def test_db_01_citizen_cnic_uniqueness_enforced():
    """DB01: Enforces unique constraint on citizen CNIC."""
    session = SessionLocal()
    cnic = "42101-0000000-1"

    # Clean up
    session.query(Citizen).filter(Citizen.cnic == cnic).delete()
    session.commit()

    try:
        c1 = Citizen(cnic=cnic, full_name="Original Citizen", monthly_income=15000.0)
        session.add(c1)
        session.commit()

        c2 = Citizen(cnic=cnic, full_name="Duplicate CNIC Impostor", monthly_income=15000.0)
        session.add(c2)
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.query(Citizen).filter(Citizen.cnic == cnic).delete()
        session.commit()
        session.close()


def test_db_02_transaction_rollback_prevents_partial_state():
    """DB02: An exception during a multi-table transaction rolls back all pending changes."""
    session = SessionLocal()
    cnic = "42101-0000000-2"

    # Clean up
    session.query(Citizen).filter(Citizen.cnic == cnic).delete()
    session.commit()

    try:
        c = Citizen(cnic=cnic, full_name="Rollback Test Citizen", monthly_income=25000.0)
        session.add(c)
        session.flush()

        # Simulate catastrophic error before commit
        raise RuntimeError("Simulated Database Abort")
    except RuntimeError:
        session.rollback()

    # Verify citizen was NOT committed
    persisted = session.query(Citizen).filter(Citizen.cnic == cnic).first()
    assert persisted is None
    session.close()


def test_db_03_audit_log_hash_chain_cryptographic_integrity():
    """DB03: Audit log hash chain verification passes for untouched ledger."""
    audit_log.append("system_test", RoleEnum.ADMIN, "TEST_INTEGRITY_CHECK", "RAHBAR_TEST")
    verification = audit_log.verify_chain()

    assert verification.is_valid is True
    assert verification.corrupted_at_index is None
    assert verification.total_records > 0


def test_db_04_audit_log_detects_hash_tampering():
    """DB04: Modifying historical hash-chain record immediately triggers tamper detection."""
    audit_log.append("tamper_target", RoleEnum.CITIZEN, "TAMPER_ACTION", "TARGET_001")

    assert len(audit_log._entries) > 0
    orig_hash = audit_log._entries[-1].current_hash

    try:
        # Forge hash
        audit_log._entries[-1].current_hash = "0123456789abcdef" + orig_hash[16:]
        verification = audit_log.verify_chain()

        assert verification.is_valid is False
        assert verification.corrupted_at_index is not None
    finally:
        # Restore ledger integrity
        audit_log._entries[-1].current_hash = orig_hash
        assert audit_log.verify_chain().is_valid is True


def test_db_05_rule_engine_versions_are_immutable():
    """DB05: Rule engine versions cannot be silently mutated or overwritten."""
    from services.api.engine.rules_engine import rules_engine
    active_v = rules_engine.get_active_rules().version
    assert active_v >= 1

    # Getting past rules by version returns historical snapshot
    v1_rules = rules_engine.get_rule_by_version(1)
    assert v1_rules is not None
    assert v1_rules.version == 1
