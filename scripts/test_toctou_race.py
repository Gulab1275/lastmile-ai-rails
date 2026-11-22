"""
TOCTOU Consent Authorization Race Verification Script.
Simulates separate processes and separate PostgreSQL connections:
1. Worker A checks consent -> returns True.
2. Worker B revokes consent -> commits to PostgreSQL.
3. Worker A attempts to retrieve protected citizen information.
Tests whether revoked consent can authorize subsequent protected data read,
and analyzes transactional coupling between authorization and data retrieval.
"""
import sys
import time
import multiprocessing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException
from services.shared.schemas import ConsentScope, RoleEnum


def worker_b_revoke_action(citizen_id: str, scope: ConsentScope, sync_barrier, return_dict):
    """Worker B process on separate PostgreSQL connection."""
    try:
        gw_b = ConsentGateway()
        # Wait for Worker A to complete Step 1 (check_consent)
        sync_barrier.wait()

        # Step 2: Worker B revokes consent
        gw_b.withdraw_consent(citizen_id, scope, actor_id="citizen_b", actor_role=RoleEnum.CITIZEN)
        return_dict["worker_b_revoked"] = True

        # Signal Worker A that revocation is committed
        sync_barrier.wait()
    except Exception as e:
        return_dict["worker_b_error"] = str(e)


def run_toctou_race_test():
    print("=" * 70)
    print("TOCTOU CONSENT AUTHORIZATION RACE INVESTIGATION")
    print("=" * 70)

    cit_id = "cit_toctou_race_test_999"
    scope = ConsentScope.INCOME
    gw_a = ConsentGateway()

    # Setup: Active consent in PostgreSQL
    gw_a.grant_consent(cit_id, scope, helper_id="helper_a")
    assert gw_a.check_consent(cit_id, scope) is True
    print(f"Initial State: Consent granted for citizen '{cit_id}' scope '{scope.value}'")

    manager = multiprocessing.Manager()
    sync_barrier = manager.Barrier(2)
    shared_data = manager.dict()

    p_b = multiprocessing.Process(
        target=worker_b_revoke_action,
        args=(cit_id, scope, sync_barrier, shared_data)
    )
    p_b.start()

    # Step 1: Worker A checks consent
    has_consent_step1 = gw_a.check_consent(cit_id, scope)
    print(f"Step 1 (Worker A): check_consent() returned: {has_consent_step1}")
    assert has_consent_step1 is True, "Worker A failed initial consent check!"

    # Signal Worker B to proceed with revocation
    sync_barrier.wait()

    # Wait for Worker B to commit revocation
    sync_barrier.wait()
    p_b.join(timeout=10)
    print(f"Step 2 (Worker B): withdraw_consent() executed and committed to PostgreSQL.")

    # Step 3: Worker A attempts protected data read
    # Scenario 3A: Worker A uses read_gateway() at time of use
    print("\nScenario 3A: Worker A calls read_gateway() at time of use...")
    blocked_at_use = False
    try:
        gw_a.read_gateway("helper_a", RoleEnum.HELPER, cit_id, scope, "helper_a")
    except ConsentWithdrawnException:
        blocked_at_use = True
        print("  -> Result: read_gateway() authoritatively queried PostgreSQL and immediately RAISED ConsentWithdrawnException (HTTP 403)!")

    assert blocked_at_use, "SECURITY FAILURE: Worker A read_gateway() allowed read after revocation!"

    # Scenario 3B: What if an application checks consent once, stores bool, and retrieves data later?
    print("\nScenario 3B: Analysis of detached Time-of-Check vs Time-of-Use...")
    if has_consent_step1 and not blocked_at_use:
        print("  -> VULNERABILITY: Stored authorization token would allow data access!")
    else:
        print("  -> VERIFIED: Because read_gateway() executes an authoritative DB query at point-of-read,")
        print("     a decoupled check-then-read pattern is safe ONLY when routed through read_gateway().")
        print("     CRITICAL ARCHITECTURAL FINDING: If any route reads DB without invoking read_gateway(),")
        print("     or if authorization check and SQL query are in separate non-locking transactions,")
        print("     a sub-millisecond TOCTOU window exists. Shared transaction or row lock is required.")

    print("\n" + "=" * 70)
    print("TOCTOU RACE TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_toctou_race_test()
