"""
Database Initialization Script for Supabase Postgres.
Provisions tables, extensions, and initial admin rule version.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from db.connection import engine, Base, SessionLocal
from db.models import (
    User, Citizen, Delegation, Consent, Case,
    Document, Decision, RuleVersion, ReviewItem,
    AuditLog, ScamMessage, EvalResult, PolicyChunk
)
from services.shared.schemas import UserRole

def init_database():
    print("[1/3] Connecting to Supabase PostgreSQL...")
    with engine.connect() as conn:
        # Enable pgvector if available
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("  --> pgvector extension enabled successfully.")
        except Exception as e:
            print(f"  --> Note on pgvector: {e}")

        # Enable uuid-ossp extension
        try:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.commit()
            print("  --> uuid-ossp extension enabled successfully.")
        except Exception as e:
            print(f"  --> Note on uuid-ossp: {e}")

    print("[2/3] Creating all database tables in Supabase...")
    Base.metadata.create_all(bind=engine)
    print("  --> Tables created successfully:")
    for table_name in Base.metadata.tables.keys():
        print(f"      - {table_name}")

    print("[3/3] Checking / Seeding default Rule Version v1...")
    session = SessionLocal()
    try:
        existing_rule = session.query(RuleVersion).filter_by(version=1).first()
        if not existing_rule:
            default_rule = RuleVersion(
                version=1,
                rule_name="Relief Cash Support Standard Eligibility 2026",
                author="system_admin",
                status="active",
                conditions=[
                    {"field": "monthly_income", "operator": "<=", "value": 45000},
                    {"field": "household_size", "operator": ">=", "value": 1},
                    {"field": "claim_amount", "operator": "<=", "value": 25000}
                ]
            )
            session.add(default_rule)
            session.commit()
            print("  --> Initial Rule Version 1 seeded successfully.")
        else:
            print("  --> Rule Version 1 already active.")
    except Exception as e:
        session.rollback()
        print(f"  --> Rule seed error: {e}")
    finally:
        session.close()

    print("\nDatabase initialization complete! Supabase is fully ready.")

if __name__ == "__main__":
    init_database()
