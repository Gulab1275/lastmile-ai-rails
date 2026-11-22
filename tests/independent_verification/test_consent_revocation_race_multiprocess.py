"""
Independent Verification: Multi-Process Consent Revocation Race.
Required sequence:
1. Worker A begins a protected data retrieval.
2. Worker B revokes consent while Worker A is in progress.
3. Worker A attempts to complete the protected read.
Verifies the outcome and documents transaction and locking behavior.
"""
import multiprocessing

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException
from services.shared.schemas import ConsentScope, RoleEnum


def worker_b_revoker_process(citizen_id: str, scope: ConsentScope, barrier, return_dict):
    """Worker B running on a separate OS process with an independent database connection."""
    try:
        gw_b = ConsentGateway()
        # Wait for Worker A to begin protected data retrieval
        barrier.wait(timeout=10)

        # Worker B simulates authenticated citizen revoking consent in PostgreSQL
        gw_b.withdraw_consent(citizen_id, scope, actor_id=citizen_id, actor_role=RoleEnum.CITIZEN)
        return_dict["revocation_committed"] = True

        # Signal Worker A that revocation is committed
        barrier.wait(timeout=10)
    except Exception as e:
        return_dict["worker_b_error"] = str(e)
        try:
            barrier.abort()
        except Exception:
            pass


def test_multiprocess_consent_revocation_race_blocks_in_progress_worker():
    """
    Verifies that when Worker A starts a protected read, and Worker B revokes consent concurrently,
    Worker A cannot complete the read once revocation is committed to PostgreSQL.
    """
    citizen_id = "cit_race_multi_process_777"
    scope = ConsentScope.INCOME
    gw_a = ConsentGateway()

    # Step 0: Ensure active consent exists in PostgreSQL
    gw_a.grant_consent(citizen_id, scope, helper_id="helper_worker_a")
    assert gw_a.check_consent(citizen_id, scope) is True

    manager = multiprocessing.Manager()
    barrier = manager.Barrier(2)
    shared_state = manager.dict()

    p_b = multiprocessing.Process(
        target=worker_b_revoker_process,
        args=(citizen_id, scope, barrier, shared_state)
    )
    p_b.start()

    # Step 1: Worker A begins protected data retrieval sequence
    # Worker A checks pre-condition
    assert gw_a.check_consent(citizen_id, scope) is True

    # Signal Worker B to execute revocation mid-flight
    barrier.wait(timeout=10)

    # Wait for Worker B to commit revocation to PostgreSQL
    barrier.wait(timeout=10)
    p_b.join(timeout=10)

    assert shared_state.get("revocation_committed") is True, f"Worker B failed: {shared_state.get('worker_b_error')}"

    # Step 3: Worker A attempts to complete protected data read via read_gateway()
    access_blocked = False
    try:
        gw_a.read_gateway(
            actor_id="helper_worker_a",
            actor_role=RoleEnum.HELPER,
            citizen_id=citizen_id,
            scope=scope,
            acting_helper_id="helper_worker_a"
        )
    except ConsentWithdrawnException:
        access_blocked = True

    assert access_blocked is True, (
        "SECURITY VULNERABILITY: Worker A completed protected read after Worker B revoked consent!"
    )
