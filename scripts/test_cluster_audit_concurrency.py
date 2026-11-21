"""
Standalone Multi-Process Concurrency Test for Database-Backed Audit Ledger.
Tests:
- Two workers appending concurrently via separate processes.
- Transaction advisory lock prevents forks and ensures single unbroken chain in PostgreSQL.
"""
import sys
import multiprocessing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.api.engine.audit_log import AuditLogLedger
from services.shared.schemas import RoleEnum


def worker_proc(worker_name: str, count: int, return_dict):
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
        return_dict[worker_name] = {"success": True, "ids": ids}
    except Exception as e:
        return_dict[worker_name] = {"success": False, "error": str(e)}


def run_concurrency_test():
    print("=" * 70)
    print("CONCURRENT AUDIT LEDGER MULTI-PROCESS VERIFICATION")
    print("=" * 70)

    manager = multiprocessing.Manager()
    results = manager.dict()

    p1 = multiprocessing.Process(target=worker_proc, args=("alpha", 5, results))
    p2 = multiprocessing.Process(target=worker_proc, args=("beta", 5, results))

    p1.start()
    p2.start()

    p1.join(timeout=20)
    p2.join(timeout=20)

    print("Worker Alpha result:", results.get("alpha"))
    print("Worker Beta result:  ", results.get("beta"))

    assert results.get("alpha", {}).get("success") is True
    assert results.get("beta", {}).get("success") is True

    ledger = AuditLogLedger()
    res = ledger.verify_chain()
    print("\nAudit Chain Verification Result:")
    print("  is_valid:           ", res.is_valid)
    print("  total_records:      ", res.total_records)
    print("  corrupted_at_index: ", res.corrupted_at_index)
    print("  head_hash:          ", res.head_hash)

    assert res.is_valid is True
    assert res.corrupted_at_index is None
    print("\n[SUCCESS] Single unbroken chain verified across concurrent worker processes!")


if __name__ == "__main__":
    run_concurrency_test()
