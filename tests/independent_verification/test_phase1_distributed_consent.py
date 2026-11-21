"""
Phase 1: Production Security Hardening - Distributed Consent Security Tests.
Tests:
1. Two independent processes accessing shared consent data via PostgreSQL.
2. Revocation from Worker A and immediate access denial in Worker B.
3. Application restart after revocation with persistent fail-closed behavior.
4. Database connection failure failing closed (access denied).
5. Concurrent grant and revoke operations under load.
6. Strict citizen and scope isolation.
"""
import multiprocessing
import threading
from unittest.mock import patch
import pytest

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException
from services.shared.schemas import ConsentScope, RoleEnum


def _worker_read(citizen_id: str, scope: ConsentScope, return_dict):
    """Independent worker process checking and reading consent."""
    try:
        gw = ConsentGateway()
        return_dict["has_consent"] = gw.check_consent(citizen_id, scope)
        try:
            gw.read_gateway("helper_sub", RoleEnum.HELPER, citizen_id, scope, "helper_sub")
            return_dict["read_allowed"] = True
        except ConsentWithdrawnException:
            return_dict["read_allowed"] = False
    except Exception as e:
        return_dict["error"] = str(e)
        return_dict["has_consent"] = False
        return_dict["read_allowed"] = False


def test_distributed_consent_two_processes_shared_data():
    """Verify two independent processes access the same authoritative PostgreSQL consent data."""
    worker_a = ConsentGateway()
    cit_id = "cit_dist_proc_101"

    worker_a.grant_consent(cit_id, ConsentScope.IDENTITY, helper_id="helper_sub")
    assert worker_a.check_consent(cit_id, ConsentScope.IDENTITY) is True

    manager = multiprocessing.Manager()
    res = manager.dict()
    p = multiprocessing.Process(target=_worker_read, args=(cit_id, ConsentScope.IDENTITY, res))
    p.start()
    p.join(timeout=15)
    if p.is_alive():
        p.terminate()
        p.join()

    assert res.get("has_consent") is True
    assert res.get("read_allowed") is True


def test_distributed_consent_worker_a_revocation_worker_b_access():
    """Worker A revokes consent; Worker B must immediately observe the revocation and be blocked."""
    worker_a = ConsentGateway()
    cit_id = "cit_dist_proc_202"

    # Grant first
    worker_a.grant_consent(cit_id, ConsentScope.BILLS, helper_id="helper_sub")

    # Worker A revokes
    worker_a.withdraw_consent(cit_id, ConsentScope.BILLS)

    manager = multiprocessing.Manager()
    res = manager.dict()
    p = multiprocessing.Process(target=_worker_read, args=(cit_id, ConsentScope.BILLS, res))
    p.start()
    p.join(timeout=15)
    if p.is_alive():
        p.terminate()
        p.join()

    # Worker B must be immediately blocked
    assert res.get("has_consent") is False
    assert res.get("read_allowed") is False


def test_distributed_consent_application_restart_persistence():
    """Grants and revocations persist authoritatively across application restart."""
    cit_id = "cit_dist_restart_303"
    gw1 = ConsentGateway()

    gw1.grant_consent(cit_id, ConsentScope.DOCUMENTS, helper_id="helper_h")
    assert gw1.check_consent(cit_id, ConsentScope.DOCUMENTS) is True

    # Simulate restart: instantiate new gateway
    gw_restarted = ConsentGateway()
    assert gw_restarted.check_consent(cit_id, ConsentScope.DOCUMENTS) is True
    assert gw_restarted.read_gateway("helper_h", RoleEnum.HELPER, cit_id, ConsentScope.DOCUMENTS, "helper_h") is True

    # Revoke in gw1
    gw1.withdraw_consent(cit_id, ConsentScope.DOCUMENTS)

    # Simulate second restart: verify revocation persisted
    gw_restarted_again = ConsentGateway()
    assert gw_restarted_again.check_consent(cit_id, ConsentScope.DOCUMENTS) is False
    with pytest.raises(ConsentWithdrawnException):
        gw_restarted_again.read_gateway("helper_h", RoleEnum.HELPER, cit_id, ConsentScope.DOCUMENTS, "helper_h")


def test_distributed_consent_database_connection_failure_fails_closed():
    """
    Requirement 7: Fail closed when consent status cannot be verified.
    Simulates database outage during check_consent and read_gateway.
    """
    gw = ConsentGateway()
    cit_id = "cit_dist_outage_404"

    # Mock SessionLocal to simulate database connection loss / OperationalError
    with patch("db.connection.SessionLocal", side_effect=RuntimeError("PostgreSQL connection refused")):
        # check_consent must return False
        assert gw.check_consent(cit_id, ConsentScope.INCOME) is False

        # read_gateway must fail closed by raising ConsentWithdrawnException (HTTP 403)
        with pytest.raises(ConsentWithdrawnException):
            gw.read_gateway("helper_1", RoleEnum.HELPER, cit_id, ConsentScope.INCOME, "helper_1")


def test_distributed_consent_concurrent_grant_and_revoke():
    """
    Requirement 8: Prevent race conditions between access and revocation.
    Executes concurrent threads performing simultaneous grant, check, and revoke operations.
    """
    gw = ConsentGateway()
    cit_id = "cit_dist_race_505"
    errors = []

    def op_grant(i):
        try:
            gw.grant_consent(cit_id, ConsentScope.PHONE, helper_id=f"helper_{i}")
        except Exception as e:
            errors.append(f"grant_{i}: {str(e)}")

    def op_revoke(i):
        try:
            gw.withdraw_consent(cit_id, ConsentScope.PHONE)
        except Exception as e:
            errors.append(f"revoke_{i}: {str(e)}")

    def op_read(i):
        try:
            gw.check_consent(cit_id, ConsentScope.PHONE)
        except Exception as e:
            errors.append(f"read_{i}: {str(e)}")

    threads = []
    for i in range(10):
        t1 = threading.Thread(target=op_grant, args=(i,))
        t2 = threading.Thread(target=op_revoke, args=(i,))
        t3 = threading.Thread(target=op_read, args=(i,))
        threads.extend([t1, t2, t3])

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(errors) == 0, f"Concurrent operations encountered errors: {errors}"


def test_distributed_consent_citizen_and_scope_isolation():
    """Verify citizen and scope isolation across PostgreSQL storage."""
    gw = ConsentGateway()
    cit_a = "cit_dist_iso_A"
    cit_b = "cit_dist_iso_B"

    gw.grant_consent(cit_a, ConsentScope.IDENTITY, helper_id="helper_1")
    gw.grant_consent(cit_a, ConsentScope.INCOME, helper_id="helper_1")
    gw.grant_consent(cit_b, ConsentScope.IDENTITY, helper_id="helper_2")
    gw.grant_consent(cit_b, ConsentScope.INCOME, helper_id="helper_2")

    # Revoke Citizen A INCOME only
    gw.withdraw_consent(cit_a, ConsentScope.INCOME)

    # Citizen A: IDENTITY is allowed, INCOME is blocked
    assert gw.read_gateway("helper_1", RoleEnum.HELPER, cit_a, ConsentScope.IDENTITY, "helper_1") is True
    with pytest.raises(ConsentWithdrawnException):
        gw.read_gateway("helper_1", RoleEnum.HELPER, cit_a, ConsentScope.INCOME, "helper_1")

    # Citizen B: both remain active and allowed
    assert gw.read_gateway("helper_2", RoleEnum.HELPER, cit_b, ConsentScope.IDENTITY, "helper_2") is True
    assert gw.read_gateway("helper_2", RoleEnum.HELPER, cit_b, ConsentScope.INCOME, "helper_2") is True
