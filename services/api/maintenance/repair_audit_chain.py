"""
Audit Chain Cryptographic Repair Tool.
Implements Task 4: Authoritative repair of cryptographic hash chain in PostgreSQL/SQLite.

Usage:
  # Dry-run mode (Default, rolls back changes):
  python -m services.api.maintenance.repair_audit_chain

  # Real commit mode:
  REPAIR_APPLY=1 REPAIR_EXPECT_FIRST_ID=771 python -m services.api.maintenance.repair_audit_chain
"""
import os
import sys
import uuid
from datetime import datetime

from sqlalchemy import text

from db.connection import SessionLocal
from db.models import AuditLog as DBAuditLog
from services.api.engine.audit_log import AUDIT_LOCK_ID, GENESIS_PREV_HASH, calculate_hash


def repair_chain() -> int:
    apply_repair = os.getenv("REPAIR_APPLY") == "1"
    expected_first_id_str = os.getenv("REPAIR_EXPECT_FIRST_ID")
    expected_first_id = int(expected_first_id_str) if expected_first_id_str else None

    print("=" * 70)
    print("RAHBAR AUDIT CHAIN REPAIR TOOL")
    print(f"Mode: {'REAL COMMIT (APPLY=1)' if apply_repair else 'DRY RUN (ROLLBACK)'}")
    if expected_first_id is not None:
        print(f"Expected First Invalid ID: {expected_first_id}")
    print("=" * 70)

    with SessionLocal() as session:
        # Step 1: Take advisory lock inside transaction if on PostgreSQL
        if session.bind and session.bind.dialect.name == "postgresql":
            print(f"Acquiring PostgreSQL transaction advisory lock (ID: {AUDIT_LOCK_ID})...")
            session.execute(text(f"SELECT pg_advisory_xact_lock({AUDIT_LOCK_ID});"))
            print("Advisory lock acquired.")

        # Step 2: Load rows ordered by id
        rows = session.query(DBAuditLog).order_by(DBAuditLog.id.asc()).all()
        total_rows = len(rows)
        print(f"Loaded {total_rows} audit_log rows from database.")

        if not rows:
            print("No rows found. Chain is empty.")
            return 0

        # Step 3: Find first invalid row using FIXED verification logic
        expected_prev = GENESIS_PREV_HASH
        first_invalid_idx = None
        first_invalid_id = None
        old_head_hash = rows[-1].current_hash

        for idx, r in enumerate(rows):
            # Check 1: prev_hash linkage
            if r.prev_hash != expected_prev:
                first_invalid_idx = idx
                first_invalid_id = r.id
                print(f"Link break at index {idx} (ID {r.id}): stored prev_hash {r.prev_hash[:16]}... != expected {expected_prev[:16]}...")
                break

            # Check 2: recompute current_hash with fixed logic
            parts = r.actor.rsplit(":", 1)
            actor_id = parts[0]
            actor_role = parts[1] if len(parts) > 1 else "system"

            if hasattr(r.timestamp, "tzinfo") and r.timestamp.tzinfo is not None:
                ts_str = r.timestamp.replace(tzinfo=None).isoformat()
            elif hasattr(r.timestamp, "isoformat"):
                ts_str = r.timestamp.isoformat()
            else:
                ts_str = str(r.timestamp)

            calc_h = calculate_hash(
                prev_hash=r.prev_hash,
                timestamp=ts_str,
                actor_id=actor_id,
                actor_role=actor_role,
                action=r.action,
                resource_id=r.target,
                details=r.details or {}
            )

            if calc_h != r.current_hash:
                first_invalid_idx = idx
                first_invalid_id = r.id
                print(f"Hash mismatch at index {idx} (ID {r.id}): stored {r.current_hash[:16]}... != calc {calc_h[:16]}...")
                break

            expected_prev = r.current_hash

        if first_invalid_idx is None:
            print("Chain is 100% valid! No repair needed.")
            return 0

        print(f"\nFirst invalid row: ID {first_invalid_id} at index {first_invalid_idx}")
        prev_valid_id = rows[first_invalid_idx - 1].id if first_invalid_idx > 0 else 0
        print(f"Rows 1..{prev_valid_id} are valid and kept UNTOUCHED.")

        # Guard checks for real commit
        if apply_repair:
            if expected_first_id is None:
                print("ABORT: REPAIR_APPLY=1 requires REPAIR_EXPECT_FIRST_ID to be explicitly set!")
                session.rollback()
                return 1
            if first_invalid_id != expected_first_id:
                print(f"ABORT: Detected first invalid ID {first_invalid_id} does not match REPAIR_EXPECT_FIRST_ID={expected_first_id}!")
                session.rollback()
                return 1

        # Step 4: From first_invalid_idx onward, recalculate in id order
        prev_hash_for_row = rows[first_invalid_idx - 1].current_hash if first_invalid_idx > 0 else GENESIS_PREV_HASH
        rows_rewritten = 0

        for r in rows[first_invalid_idx:]:
            parts = r.actor.rsplit(":", 1)
            actor_id = parts[0]
            actor_role = parts[1] if len(parts) > 1 else "system"

            if hasattr(r.timestamp, "tzinfo") and r.timestamp.tzinfo is not None:
                ts_str = r.timestamp.replace(tzinfo=None).isoformat()
            elif hasattr(r.timestamp, "isoformat"):
                ts_str = r.timestamp.isoformat()
            else:
                ts_str = str(r.timestamp)

            new_current_h = calculate_hash(
                prev_hash=prev_hash_for_row,
                timestamp=ts_str,
                actor_id=actor_id,
                actor_role=actor_role,
                action=r.action,
                resource_id=r.target,
                details=r.details or {}
            )

            r.prev_hash = prev_hash_for_row
            r.current_hash = new_current_h
            prev_hash_for_row = new_current_h
            rows_rewritten += 1

        # Step 5: Append one new repair record
        repair_now = datetime.utcnow()
        repair_details = {
            "reason": "Cryptographic hash chain repair for post-fork and actor split re-linkage",
            "first_row_id": first_invalid_id,
            "rows_rewritten": rows_rewritten,
            "old_head_hash": old_head_hash,
            "date": repair_now.isoformat(),
            "note": "Events, timestamps, actors and details are unchanged. Backup preserved before repair."
        }

        repair_hash = calculate_hash(
            prev_hash=prev_hash_for_row,
            timestamp=repair_now.isoformat(),
            actor_id="system",
            actor_role="admin",
            action="AUDIT_CHAIN_REPAIRED",
            resource_id="RAHBAR_PLATFORM",
            details=repair_details
        )

        repair_entry = DBAuditLog(
            prev_hash=prev_hash_for_row,
            current_hash=repair_hash,
            actor="system:admin",
            action="AUDIT_CHAIN_REPAIRED",
            target="RAHBAR_PLATFORM",
            result="SUCCESS",
            request_id=f"aud_repair_{uuid.uuid4().hex[:12]}",
            timestamp=repair_now,
            details=repair_details
        )
        session.add(repair_entry)
        session.flush()

        # Step 6: Re-verify whole chain in the same transaction
        all_verify_rows = session.query(DBAuditLog).order_by(DBAuditLog.id.asc()).all()
        chk_prev = GENESIS_PREV_HASH
        for v_idx, v_row in enumerate(all_verify_rows):
            if v_row.prev_hash != chk_prev:
                print(f"VERIFICATION FAILURE: link break at index {v_idx} (ID {v_row.id})")
                session.rollback()
                return 1

            v_parts = v_row.actor.rsplit(":", 1)
            v_act_id = v_parts[0]
            v_act_role = v_parts[1] if len(v_parts) > 1 else "system"

            if hasattr(v_row.timestamp, "tzinfo") and v_row.timestamp.tzinfo is not None:
                v_ts = v_row.timestamp.replace(tzinfo=None).isoformat()
            elif hasattr(v_row.timestamp, "isoformat"):
                v_ts = v_row.timestamp.isoformat()
            else:
                v_ts = str(v_row.timestamp)

            v_calc = calculate_hash(
                prev_hash=v_row.prev_hash,
                timestamp=v_ts,
                actor_id=v_act_id,
                actor_role=v_act_role,
                action=v_row.action,
                resource_id=v_row.target,
                details=v_row.details or {}
            )
            if v_calc != v_row.current_hash:
                print(f"VERIFICATION FAILURE: hash mismatch at index {v_idx} (ID {v_row.id})")
                session.rollback()
                return 1

            chk_prev = v_row.current_hash

        print(f"\nWhole chain re-verification succeeded! Total records: {len(all_verify_rows)}.")
        print(f"Rows rewritten: {rows_rewritten}. New head hash: {chk_prev[:16]}...")

        # Step 7: Commit if real apply, otherwise rollback
        if apply_repair:
            session.commit()
            print("REPAIR COMMITTED TO DATABASE SUCCESSFULLY.")
        else:
            session.rollback()
            print("DRY RUN COMPLETE: Transaction rolled back. No database changes were made.")

        return 0


if __name__ == "__main__":
    sys.exit(repair_chain())
