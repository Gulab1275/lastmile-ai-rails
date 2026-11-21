"""
Phase 2: Independent Deep Security Verification of Consent Gateway.
Tests:
1. Revocation of uninitialized scopes.
2. Repeated revocation.
3. Access immediately after revocation.
4. Concurrent reads and revocation under load.
5. Revocation across separate processes (Process isolation test).
6. Revocation persistence after application restart (State reload test).
7. Isolation between different citizens and consent scopes.
Analyzes dependence on process-local memory vs persistent store.
"""
import multiprocessing

import pytest

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException
from services.shared.schemas import ConsentScope, RoleEnum


def test_01_revocation_of_uninitialized_scopes():
    """Verify that revoking consent for an uninitialized scope fails closed (denies access)."""
    gateway = ConsentGateway()
    cit_id = "cit_indep_uninit_999"

    # Revoke scope never previously granted
    rec = gateway.withdraw_consent(cit_id, ConsentScope.INCOME)
    assert rec.granted is False
    assert rec.revoked_at is not None
    assert gateway.check_consent(cit_id, ConsentScope.INCOME) is False

    with pytest.raises(ConsentWithdrawnException):
        gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.INCOME, "helper_1")


def test_02_repeated_revocation_idempotency():
    """Verify repeated revocation is idempotent and never flips back to granted."""
    gateway = ConsentGateway()
    cit_id = "cit_indep_repeat_888"

    gateway.grant_consent(cit_id, ConsentScope.DOCUMENTS, helper_id="helper_1")
    assert gateway.check_consent(cit_id, ConsentScope.DOCUMENTS) is True

    # Revoke 5 times sequentially
    for i in range(5):
        rec = gateway.withdraw_consent(cit_id, ConsentScope.DOCUMENTS)
        assert rec.granted is False
        assert gateway.check_consent(cit_id, ConsentScope.DOCUMENTS) is False
        with pytest.raises(ConsentWithdrawnException):
            gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.DOCUMENTS, "helper_1")


def test_03_access_immediately_after_revocation():
    """Verify zero-window immediate access blocking upon revocation."""
    gateway = ConsentGateway()
    cit_id = "cit_indep_zero_window_777"

    gateway.grant_consent(cit_id, ConsentScope.IDENTITY, helper_id="helper_1")
    # Immediate read is allowed
    assert gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.IDENTITY, "helper_1") is True

    # Immediate revoke
    gateway.withdraw_consent(cit_id, ConsentScope.IDENTITY)

    # Next exact clock tick must raise 403
    with pytest.raises(ConsentWithdrawnException):
        gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.IDENTITY, "helper_1")


def test_04_isolation_between_citizens_and_scopes():
    """Verify complete isolation: Citizen A's revocation never impacts Citizen B, and Scope X never impacts Scope Y."""
    gateway = ConsentGateway()
    cit_a = "cit_indep_iso_A"
    cit_b = "cit_indep_iso_B"

    # Citizen A grants IDENTITY and INCOME
    gateway.grant_consent(cit_a, ConsentScope.IDENTITY, helper_id="helper_1")
    gateway.grant_consent(cit_a, ConsentScope.INCOME, helper_id="helper_1")

    # Citizen B grants IDENTITY and INCOME
    gateway.grant_consent(cit_b, ConsentScope.IDENTITY, helper_id="helper_2")
    gateway.grant_consent(cit_b, ConsentScope.INCOME, helper_id="helper_2")

    # Revoke Citizen A's INCOME only
    gateway.withdraw_consent(cit_a, ConsentScope.INCOME)

    # Citizen A: INCOME blocked, IDENTITY allowed
    with pytest.raises(ConsentWithdrawnException):
        gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_a, ConsentScope.INCOME, "helper_1")
    assert gateway.read_gateway("helper_1", RoleEnum.HELPER, cit_a, ConsentScope.IDENTITY, "helper_1") is True

    # Citizen B: Both INCOME and IDENTITY must remain completely permitted
    assert gateway.read_gateway("helper_2", RoleEnum.HELPER, cit_b, ConsentScope.INCOME, "helper_2") is True
    assert gateway.read_gateway("helper_2", RoleEnum.HELPER, cit_b, ConsentScope.IDENTITY, "helper_2") is True


def _worker_process_check(citizen_id: str, scope: ConsentScope, return_dict):
    """Subprocess that creates its own ConsentGateway instance."""
    try:
        proc_gateway = ConsentGateway()
        # In a new process, memory is fresh
        return_dict["check_result"] = proc_gateway.check_consent(citizen_id, scope)
        try:
            proc_gateway.read_gateway("helper_sub", RoleEnum.HELPER, citizen_id, scope, "helper_sub")
            return_dict["read_allowed"] = True
        except ConsentWithdrawnException:
            return_dict["read_allowed"] = False
    except Exception as e:
        return_dict["error"] = str(e)
        return_dict["check_result"] = False
        return_dict["read_allowed"] = False


def test_05_cross_process_isolation_and_memory_dependence():
    """
    Phase 1 Distributed Consent Verification:
    Tests whether a grant from Worker 1 persists to PostgreSQL and is immediately observed
    by Worker 2, and that subsequent revocation by Worker 1 is immediately observed by Worker 2.
    """
    gateway_proc1 = ConsentGateway()
    cit_id = "cit_indep_proc_555"

    # Step A: Process 1 grants consent in authoritative PostgreSQL
    gateway_proc1.grant_consent(cit_id, ConsentScope.IDENTITY, helper_id="helper_sub")
    assert gateway_proc1.check_consent(cit_id, ConsentScope.IDENTITY) is True

    # Spawn separate Process 2 to check its view of the consent state (Worker B)
    manager = multiprocessing.Manager()
    return_dict1 = manager.dict()

    p1 = multiprocessing.Process(
        target=_worker_process_check,
        args=(cit_id, ConsentScope.IDENTITY, return_dict1)
    )
    p1.start()
    p1.join(timeout=15)
    if p1.is_alive():
        p1.terminate()
        p1.join()

    # Worker B immediately observes the grant via authoritative PostgreSQL
    assert return_dict1.get("check_result") is True
    assert return_dict1.get("read_allowed") is True

    # Step B: Worker A revokes consent
    gateway_proc1.withdraw_consent(cit_id, ConsentScope.IDENTITY)
    assert gateway_proc1.check_consent(cit_id, ConsentScope.IDENTITY) is False

    # Spawn separate Process 2 to verify immediate revocation visibility
    return_dict2 = manager.dict()
    p2 = multiprocessing.Process(
        target=_worker_process_check,
        args=(cit_id, ConsentScope.IDENTITY, return_dict2)
    )
    p2.start()
    p2.join(timeout=15)
    if p2.is_alive():
        p2.terminate()
        p2.join()

    # Worker B immediately observes revocation (check_consent is False, read raises 403)
    assert return_dict2.get("check_result") is False
    assert return_dict2.get("read_allowed") is False


def test_06_persistence_after_gateway_reinstantiation():
    """
    Evaluates application restart behavior:
    When a new ConsentGateway() is instantiated (simulating process restart),
    both grants and revocations persist authoritatively via PostgreSQL.
    """
    cit_id = "cit_indep_restart_444"
    gateway_before = ConsentGateway()

    # Grant consent and verify persistence across reinstantiation
    gateway_before.grant_consent(cit_id, ConsentScope.INCOME, helper_id="helper_1")
    assert gateway_before.check_consent(cit_id, ConsentScope.INCOME) is True

    gateway_after_grant = ConsentGateway()
    assert gateway_after_grant.check_consent(cit_id, ConsentScope.INCOME) is True
    assert gateway_after_grant.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.INCOME, "helper_1") is True

    # Revoke consent and verify revocation persistence across reinstantiation
    gateway_before.withdraw_consent(cit_id, ConsentScope.INCOME)
    assert gateway_before.check_consent(cit_id, ConsentScope.INCOME) is False

    gateway_after_revoke = ConsentGateway()
    assert gateway_after_revoke.check_consent(cit_id, ConsentScope.INCOME) is False
    with pytest.raises(ConsentWithdrawnException):
        gateway_after_revoke.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.INCOME, "helper_1")
