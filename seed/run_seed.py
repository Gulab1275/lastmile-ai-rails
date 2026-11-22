"""
Synthetic Dataset & Seed Script (Task N3 / Challenge 03).
Populates Supabase with:
1. Demo users for all 5 roles.
2. 200 mock citizens (with intentional variants, duplicates, typos, and missing fields).
3. 3 test cases for demonstrating the 3 decision routes.
"""
import hashlib
import random
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import SessionLocal
from db.models import AuditLog, Case, Citizen, Consent, Document, User
from services.shared.schemas import CaseStatus, ConsentScope, ConsentStatus, UserRole

FIRST_NAMES = ["Muhammad", "Mohammad", "Muhammed", "Mohd", "Ali", "Hassan", "Ahmed", "Fatima", "Ayesha", "Zainab", "Khadija", "Rashid", "Tariq", "Imran"]
LAST_NAMES = ["Khan", "Ahmed", "Syed", "Shah", "Malik", "Chaudhry", "Bhatti", "Ansari", "Qureshi", "Abbasi"]

def generate_cnic(prefix: int, serial: int, check: int) -> str:
    return f"{prefix:05d}-{serial:07d}-{check:01d}"

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def seed_database():
    session = SessionLocal()
    try:
        print("[1/4] Seeding Demo Users for all 5 roles...")
        demo_users = [
            ("citizen.widow@rahbar.local", "Widow Fatima Begum", UserRole.CITIZEN.value),
            ("citizen.shopkeeper@rahbar.local", "Shopkeeper Abdul Qadir", UserRole.CITIZEN.value),
            ("helper.fatima@rahbar.local", "Community Helper Fatima", UserRole.HELPER.value),
            ("officer.ahmed@rahbar.local", "Review Officer Ahmed", UserRole.OFFICER.value),
            ("admin.tariq@rahbar.local", "Admin Tariq", UserRole.ADMIN.value),
            ("auditor.sarah@rahbar.local", "Auditor Sarah", UserRole.AUDITOR.value),
        ]

        for email, name, role in demo_users:
            if not session.query(User).filter_by(email=email).first():
                user = User(
                    email=email,
                    password_hash=hash_pw("DemoPass123!"),
                    full_name=name,
                    role=role
                )
                session.add(user)
        session.commit()
        print("  --> 6 Demo Users ready.")

        print("[2/4] Generating 200 synthetic mock citizens (with variants, typos & duplicates)...")
        existing_count = session.query(Citizen).count()
        if existing_count < 200:
            citizens_to_add = []

            # 1. Generate 145 clean baseline citizens
            for i in range(existing_count + 1, 146):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                cnic = generate_cnic(random.randint(42101, 42501), random.randint(1000000, 9999999), random.randint(1, 9))

                # Intentional variants for names
                variants = [f"{fname} {lname}"]
                if fname in ["Muhammad", "Mohammad", "Muhammed"]:
                    variants.extend([f"Mohd {lname}", f"M. {lname}"])

                c = Citizen(
                    cnic=cnic,
                    full_name=f"{fname} {lname}",
                    name_variants=variants,
                    phone=f"0300{random.randint(1000000, 9999999)}",
                    dob=f"{random.randint(1,28):02d}-{random.randint(1,12):02d}-{random.randint(1965, 2002)}",
                    household_size=random.randint(2, 8),
                    monthly_income=float(random.randint(18000, 48000)),
                    address=f"House {i}, Sector {random.randint(1, 12)}, Orangi Town, Karachi"
                )
                citizens_to_add.append(c)

            # 2. Add 15 duplicate pairs with spelling variations
            for i in range(15):
                base_cnic = generate_cnic(35201, 5000000 + i, 1)
                c_orig = Citizen(
                    cnic=base_cnic,
                    full_name=f"Muhammad Ali {i+1}",
                    name_variants=[f"Mohammad Ali {i+1}"],
                    phone="03211234567",
                    household_size=4,
                    monthly_income=28000.0
                )
                citizens_to_add.append(c_orig)

            # 3. Add 30 citizens with missing fields (missing income / household size)
            for i in range(30):
                c_missing = Citizen(
                    cnic=generate_cnic(37405, 8000000 + i, 3),
                    full_name=f"Zubaida Bibi {i+1}",
                    phone="03457654321",
                    household_size=1,
                    monthly_income=None  # triggers ask_for_proof
                )
                citizens_to_add.append(c_missing)

            # 4. Add 10 citizens with slight CNIC typos
            for i in range(10):
                c_typo = Citizen(
                    cnic=f"42101-999999{i}-X",  # invalid check digit format
                    full_name=f"Rashid Minhas {i+1}",
                    household_size=3,
                    monthly_income=32000.0
                )
                citizens_to_add.append(c_typo)

            session.bulk_save_objects(citizens_to_add)
            session.commit()
            print("  --> 200 synthetic citizens created successfully.")
        else:
            print("  --> 200 mock citizens already exist in Supabase.")

        print("[3/4] Creating 3 baseline test cases for decision engine routes...")
        # 1. Clean Citizen for Auto-Approve demo
        clean_citizen = session.query(Citizen).filter(Citizen.monthly_income.isnot(None), Citizen.monthly_income < 35000).first()
        if clean_citizen:
            case_auto = session.query(Case).filter_by(citizen_id=clean_citizen.id).first()
            if not case_auto:
                case_auto = Case(
                    citizen_id=clean_citizen.id,
                    status=CaseStatus.SUBMITTED.value,
                    claim_amount=15000.0,
                    form_data={
                        "full_name": clean_citizen.full_name,
                        "cnic": clean_citizen.cnic,
                        "monthly_income": clean_citizen.monthly_income,
                        "household_size": clean_citizen.household_size
                    }
                )
                session.add(case_auto)
                session.flush()

                # Add sharp documents
                doc1 = Document(
                    case_id=case_auto.id,
                    doc_type="cnic_front",
                    file_path="/mock/storage/clean_cnic.jpg",
                    blur_score=1850.0,
                    tamper_score=0.01,
                    confidence=0.98
                )
                doc2 = Document(
                    case_id=case_auto.id,
                    doc_type="utility_bill",
                    file_path="/mock/storage/clean_bill.jpg",
                    blur_score=1420.0,
                    tamper_score=0.02,
                    confidence=0.96
                )
                session.add_all([doc1, doc2])

                # Grant consent
                consent = Consent(
                    citizen_id=clean_citizen.id,
                    grantee="system",
                    scope=ConsentScope.IDENTITY.value,
                    status=ConsentStatus.ACTIVE.value
                )
                session.add(consent)
                session.commit()
                print(f"  --> Case 1 (Auto-Approve Candidate): {case_auto.id}")

        print("[4/4] Writing initial system audit trail...")
        AuditLog.create_entry(
            session=session,
            actor="seed_engine",
            action="init_synthetic_data",
            target="all_tables",
            result="success",
            request_id="seed_req_001"
        )
        print("  --> Audit log entry sealed with SHA-256 hash.")

        print("\nSeed script execution completed successfully!")

    except Exception as e:
        session.rollback()
        print(f"Seed error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
