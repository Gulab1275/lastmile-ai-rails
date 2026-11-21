"""
Supabase Keep-Alive & Health Ping Script (Task N1).
Periodically sends a lightweight heartbeat query to Supabase Postgres
to prevent free-tier project auto-pausing and verify connection pool health.

Usage:
  python scripts/keepalive_ping.py            # Single ping
  python scripts/keepalive_ping.py --loop 300 # Periodic ping every 300s
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import SessionLocal, engine


def ping_database() -> bool:
    """Executes a lightweight heartbeat query and checks connection pool status."""
    now = datetime.now(timezone.utc).isoformat()
    session = SessionLocal()
    try:
        start_time = time.time()
        session.execute(text("SELECT 1 AS heartbeat, version() AS pg_ver;")).fetchone()
        latency_ms = (time.time() - start_time) * 1000

        # Check table count
        tables_res = session.execute(text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
        )).scalar()

        print(f"[{now}] [OK] Supabase Heartbeat: {latency_ms:.1f}ms | Tables: {tables_res} | Pool: {engine.pool.status()}")
        return True
    except Exception as e:
        print(f"[{now}] [ERROR] Supabase Ping Failed: {e}", file=sys.stderr)
        return False
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Supabase Keep-Alive Ping")
    parser.add_argument("--loop", type=int, default=0, help="Interval in seconds for continuous ping loop (0 = single ping)")
    args = parser.parse_args()

    if args.loop <= 0:
        success = ping_database()
        sys.exit(0 if success else 1)
    else:
        print(f"[*] Starting Supabase keep-alive loop (interval: {args.loop}s)... Press Ctrl+C to stop.")
        while True:
            ping_database()
            time.sleep(args.loop)


if __name__ == "__main__":
    main()
