import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db.connection import engine

with engine.connect() as conn:
    cols = conn.execute(text("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'policy_chunks'")).fetchall()
    print("policy_chunks columns:")
    for c in cols:
        print(f"  - {c[0]}: {c[1]} ({c[2]})")

    count = conn.execute(text("SELECT count(*) FROM policy_chunks")).scalar()
    print(f"Current rows in policy_chunks: {count}")

    if count > 0:
        rows = conn.execute(text("SELECT id, document_name, page_number, content, embedding_json FROM policy_chunks LIMIT 2")).fetchall()
        for r in rows:
            print(f"Row: {r[1]} p.{r[2]} | {r[3][:60]}... | Embedding len: {len(r[4]) if r[4] else 'None'}")
