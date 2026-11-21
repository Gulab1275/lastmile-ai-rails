import os
import urllib.parse
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env (if present)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Determine the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# If running under Alembic (migration generation) or psycopg is unavailable, fall back to SQLite for safety
if not DATABASE_URL or "alembic" in sys.argv[0]:
    DATABASE_URL = "sqlite:///test_migrate.db"
elif "your_password" in DATABASE_URL:
    # Preserve existing fallback logic for local development (only when psycopg is available)
    db_pass = os.getenv("SUPABASE_DB_PASSWORD", "fast##ai#1234")
    encoded_pass = urllib.parse.quote_plus(db_pass)
    DATABASE_URL = f"postgresql+psycopg://postgres:{encoded_pass}@db.rhlvnyqgrbjsvlbzljhz.supabase.co:5432/postgres"
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Supabase direct connection engine (or SQLite for migrations)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_health():
    """Health check ping to Supabase Postgres."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return {"status": "healthy", "postgres": result == 1}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
