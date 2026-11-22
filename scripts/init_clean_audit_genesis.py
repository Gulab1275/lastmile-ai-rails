"""
Initializes clean Genesis block in PostgreSQL audit_log table using ORM.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import SessionLocal, engine
from db.models import AuditLog as DBAuditLog
from sqlalchemy import text
from services.api.engine.audit_log import calculate_hash, GENESIS_PREV_HASH

genesis_ts = datetime(2026, 11, 20, 18, 0, 0)
genesis_details = {"version": "1.0.0", "event": "Coders Cup '26 DPI Initiation"}
genesis_hash = calculate_hash(
    prev_hash=GENESIS_PREV_HASH,
    timestamp=genesis_ts.isoformat(),
    actor_id="system",
    actor_role="admin",
    action="GENESIS_SYSTEM_START",
    resource_id="RAHBAR_PLATFORM",
    details=genesis_details
)

with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE audit_log RESTART IDENTITY;"))
    conn.commit()

with SessionLocal() as session:
    entry = DBAuditLog(
        prev_hash=GENESIS_PREV_HASH,
        current_hash=genesis_hash,
        actor="system:admin",
        action="GENESIS_SYSTEM_START",
        target="RAHBAR_PLATFORM",
        result="SUCCESS",
        request_id="audit_genesis_0000",
        timestamp=genesis_ts,
        details=genesis_details
    )
    session.add(entry)
    session.commit()
    print("Clean Genesis initialized via ORM. Row ID:", entry.id)
    print("Genesis hash:", entry.current_hash)
