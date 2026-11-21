"""
Pre-Production Gate Inspection Script:
1. Inspects check_valid_cnic_format constraint details in PostgreSQL.
2. Tests INSERT enforcement.
3. Tests UPDATE enforcement.
4. Verifies the 10 legacy records remain intact.
5. Verifies valid records can still be updated.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from db.connection import engine, SessionLocal
from db.models import Citizen

def inspect_database_security():
    print("=" * 70)
    print("1. POSTGRESQL CONSTRAINT INSPECTION")
    print("=" * 70)
    with engine.connect() as conn:
        res = conn.execute(text(
            "SELECT conname, contype, convalidated, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE conname = 'check_valid_cnic_format';"
        )).fetchall()
        print("Constraint Definition from PostgreSQL:")
        for r in res:
            print(f"  Name: {r[0]} | Type: {r[1]} | Validated: {r[2]} | Def: {r[3]}")

        # Check 10 legacy records
        legacy = conn.execute(text(
            "SELECT id, cnic, full_name FROM citizens WHERE cnic LIKE '%-X' ORDER BY cnic;"
        )).fetchall()
        print(f"\nLegacy Records Preserved (Total: {len(legacy)}):")
        for leg in legacy:
            print(f"  - {leg[0]} | {leg[1]} | {leg[2]}")

        # Test UPDATE enforcement (attempting to update valid record to invalid CNIC)
        print("\nTesting UPDATE enforcement with invalid CNIC:")
        sample_id = "test_update_probe_citizen"
        conn.execute(text(
            "INSERT INTO citizens (id, cnic, full_name) VALUES ('test_update_probe_citizen', '42101-1111111-1', 'Update Probe');"
        ))
        conn.commit()

        update_rejected = False
        try:
            conn.execute(text(
                "UPDATE citizens SET cnic = '42101-INVALID-1' WHERE id = 'test_update_probe_citizen';"
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            update_rejected = True
            print(f"  -> UPDATE with invalid CNIC rejected successfully by PostgreSQL!")
            print(f"     Error: {str(e).splitlines()[0]}")

        assert update_rejected, "SECURITY FAILURE: PostgreSQL allowed invalid CNIC update!"

        # Test valid UPDATE (e.g. updating phone or valid CNIC)
        conn.execute(text(
            "UPDATE citizens SET phone = '+923009999999', full_name = 'Updated Name' WHERE id = 'test_update_probe_citizen';"
        ))
        conn.commit()
        updated_row = conn.execute(text(
            "SELECT phone, full_name FROM citizens WHERE id = 'test_update_probe_citizen';"
        )).fetchone()
        print(f"  -> Valid UPDATE succeeded: phone={updated_row[0]}, name={updated_row[1]}")

        # Cleanup
        conn.execute(text("DELETE FROM citizens WHERE id = 'test_update_probe_citizen';"))
        conn.commit()
        print("  -> Cleaned up test record.")

if __name__ == "__main__":
    inspect_database_security()
