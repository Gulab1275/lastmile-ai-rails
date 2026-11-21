"""
Database Migration: Add Strict ASCII CNIC CheckConstraint.
Safe migration script conforming to Phase 2 requirements:
1. Inspects existing records before applying constraints.
2. Preserves all existing records (does NOT delete or silently alter invalid legacy records).
3. Applies PostgreSQL CHECK constraint with NOT VALID clause so legacy records remain intact
   while all new and updated records are strictly validated at the database layer.
4. Verifies database-level enforcement by testing that invalid direct inserts fail.
"""
import sys
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from db.connection import engine, SessionLocal
from db.models import Citizen


CNIC_REGEX = re.compile(r"^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$")


def run_migration():
    print("=" * 70)
    print("RAHBAR DPI: CNIC DATABASE CONSTRAINT MIGRATION")
    print("=" * 70)

    with engine.connect() as conn:
        # Step 1: Inspect existing records
        print("\n[Step 1/4] Inspecting existing records in 'citizens' table...")
        rows = conn.execute(text("SELECT id, cnic, full_name FROM citizens ORDER BY cnic;")).fetchall()
        total_count = len(rows)
        print(f"  -> Total citizen records found: {total_count}")

        valid_records = []
        invalid_records = []
        for r in rows:
            cnic_val = r[1] or ""
            if CNIC_REGEX.match(cnic_val):
                valid_records.append(r)
            else:
                invalid_records.append(r)

        print(f"  -> Valid ASCII CNIC records:   {len(valid_records)}")
        print(f"  -> Non-conforming legacy records: {len(invalid_records)}")

        if invalid_records:
            print("\n  [SAFETY NOTICE] The following legacy records do not conform to standard format:")
            for inv in invalid_records:
                print(f"     - ID: {inv[0]} | CNIC: {inv[1]} | Name: {inv[2]}")
            print("  -> Under Phase 2 requirements, these records will NOT be deleted or altered.")
            print("  -> PostgreSQL 'NOT VALID' constraint clause will be used to preserve them safely.")

        # Step 2: Apply constraint safely using NOT VALID
        print("\n[Step 2/4] Applying database-level CHECK constraint...")
        # Check if constraint already exists
        check_existing = conn.execute(text("""
            SELECT conname FROM pg_constraint 
            WHERE conname = 'check_valid_cnic_format' 
            AND conrelid = 'citizens'::regclass;
        """)).fetchall()

        if check_existing:
            print("  -> Constraint 'check_valid_cnic_format' already exists. Dropping to re-apply cleanly...")
            conn.execute(text("ALTER TABLE citizens DROP CONSTRAINT check_valid_cnic_format;"))
            conn.commit()

        # Add NOT VALID constraint: enforces check on all new INSERTs/UPDATEs without failing on legacy rows
        sql_add_constraint = """
            ALTER TABLE citizens 
            ADD CONSTRAINT check_valid_cnic_format 
            CHECK (cnic ~ '^[0-9]{5}-[0-9]{7}-[0-9]{1}$' OR cnic ~ '^[0-9]{13}$') 
            NOT VALID;
        """
        conn.execute(text(sql_add_constraint))
        conn.commit()
        print("  -> Successfully added CHECK constraint 'check_valid_cnic_format' (NOT VALID).")

        # Step 3: Verify existing records are preserved
        print("\n[Step 3/4] Verifying legacy records preservation...")
        post_count = conn.execute(text("SELECT count(*) FROM citizens;")).scalar()
        assert post_count == total_count, f"Record count changed from {total_count} to {post_count}!"
        print(f"  -> All {post_count} records remain intact in database. Zero data loss verified.")

        # Step 4: Verify that invalid direct SQL insertions are blocked
        print("\n[Step 4/4] Verifying database-level enforcement on new writes...")
        test_bad_id = "test_bad_cnic_migration_probe"
        try:
            conn.execute(text("""
                INSERT INTO citizens (id, cnic, full_name, household_size, monthly_income)
                VALUES ('test_bad_cnic_migration_probe', '42101-123456A-1', 'Probe Citizen', 1, 0);
            """))
            conn.commit()
            raise RuntimeError("Database-level enforcement FAILED: invalid CNIC was accepted!")
        except Exception as e:
            conn.rollback()
            err_msg = str(e)
            if "check_valid_cnic_format" in err_msg or "CheckViolation" in err_msg or "violates check constraint" in err_msg:
                print("  -> Verified: Direct SQL insert of invalid CNIC ('42101-123456A-1') successfully rejected by check constraint!")
                print(f"     Database Error: {err_msg.splitlines()[0]}")
            else:
                raise e

        # Test valid insert
        test_good_id = "test_good_cnic_migration_probe"
        conn.execute(text("""
            INSERT INTO citizens (id, cnic, full_name, household_size, monthly_income)
            VALUES ('test_good_cnic_migration_probe', '42101-8888888-1', 'Valid Probe Citizen', 1, 0);
        """))
        conn.commit()
        print("  -> Verified: Direct SQL insert of valid CNIC ('42101-8888888-1') succeeded.")
        # Cleanup probe
        conn.execute(text("DELETE FROM citizens WHERE id = 'test_good_cnic_migration_probe';"))
        conn.commit()
        print("  -> Cleaned up test probe.")

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
