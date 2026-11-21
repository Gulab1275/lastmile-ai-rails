import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env (if present)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Determine the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    if any("alembic" in arg.lower() for arg in sys.argv):
        DATABASE_URL = "sqlite:///test_migrate.db"
    else:
        raise RuntimeError(
            "DATABASE_URL environment variable is required but not set. "
            "Please provide a valid database connection string (e.g. postgresql://user:pass@host:5432/db)."
        )

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Direct connection engine (configured with production pool settings)
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
    """Health check ping to database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return {"status": "healthy", "postgres": result == 1}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
