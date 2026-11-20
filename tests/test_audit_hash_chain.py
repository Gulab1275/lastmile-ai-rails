"""
Tests for Cryptographic Hash-Chained Audit Ledger and Tamper Detection.
Implements Hackathon Challenge 05: Explain and Audit.
"""
from services.api.engine.audit_log import AuditLogLedger
from services.shared.schemas import RoleEnum


def test_audit_chain_validity_untampered():
    """Verifies that an uncorrupted audit chain passes verification."""
    ledger = AuditLogLedger()
    ledger.append("usr_1", RoleEnum.CITIZEN, "CASE_CREATED", "cas_001", {"amount": 12000})
    ledger.append("usr_2", RoleEnum.OFFICER, "CASE_APPROVED", "cas_001", {"notes": "Approved"})

    result = ledger.verify_chain()
    assert result.is_valid is True
    assert result.corrupted_at_index is None
    assert result.total_records >= 3  # Genesis + 2 entries


def test_audit_chain_tamper_detection():
    """
    CRITICAL AUDIT CAPABILITY:
    If a record's details or previous hash are tampered with,
    verify_chain() MUST immediately flag the chain as invalid
    and identify the exact corrupted index.
    """
    ledger = AuditLogLedger()
    ledger.append("usr_1", RoleEnum.CITIZEN, "CASE_CREATED", "cas_001", {"amount": 12000})
    ledger.append("usr_2", RoleEnum.OFFICER, "CASE_APPROVED", "cas_001", {"notes": "Approved"})

    # Malicious tampering: altering the amount of a past disbursement
    ledger._entries[1].details = {"amount": 9999999}  # Tampered!

    result = ledger.verify_chain()
    assert result.is_valid is False
    assert result.corrupted_at_index == 1
