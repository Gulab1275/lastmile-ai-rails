"""
Pytest configuration and fixtures.
Provides test client and pre-authenticated authorization headers for all 5 roles:
- Citizen
- Helper
- Officer
- Admin
- Auditor
"""
import os
import sqlite3
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Ensure repository root is on sys.path for test discovery in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Task 4 & Task 1: Dedicated clean test database and distinct cryptographic keys
isolated_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_isolated_suite.db"))
if os.path.exists(isolated_db_path):
    try:
        os.remove(isolated_db_path)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{isolated_db_path}"
os.environ["SECRET_KEY"] = "test-fixture-suite-jwt-secret-key-min32chars-token"
os.environ["APPROVAL_TOKEN_SECRET"] = "test-fixture-suite-approval-token-secret-distinct-min32chars"
os.environ["AUDIT_CHECKPOINT_KEY"] = "test-fixture-suite-audit-checkpoint-key-distinct-min32chars"

from db.connection import Base, engine  # noqa: E402
from services.api.main import app  # noqa: E402
from services.api.security.auth import _USERS_BY_USERNAME, create_access_token  # noqa: E402
from services.shared.schemas import RoleEnum  # noqa: E402


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce foreign key constraints on all SQLite connections."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


Base.metadata.create_all(bind=engine)

# Seed audit ledger with Genesis block if empty
from services.api.engine.audit_log import audit_log  # noqa: E402

audit_log._entries.clear()
audit_log._sync_from_db()


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped TestClient."""
    return TestClient(app)


@pytest.fixture
def citizen_headers() -> dict:
    user_id = _USERS_BY_USERNAME["citizen_parveen"]
    token = create_access_token(
        user_id=user_id,
        username="citizen_parveen",
        role=RoleEnum.CITIZEN
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def helper_headers() -> dict:
    user_id = _USERS_BY_USERNAME["helper_shazia"]
    token = create_access_token(
        user_id=user_id,
        username="helper_shazia",
        role=RoleEnum.HELPER
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def officer_headers() -> dict:
    user_id = _USERS_BY_USERNAME["officer_aslam"]
    token = create_access_token(
        user_id=user_id,
        username="officer_aslam",
        role=RoleEnum.OFFICER
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers() -> dict:
    user_id = _USERS_BY_USERNAME["admin_ayesha"]
    token = create_access_token(
        user_id=user_id,
        username="admin_ayesha",
        role=RoleEnum.ADMIN
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auditor_headers() -> dict:
    user_id = _USERS_BY_USERNAME["auditor_iqbal"]
    token = create_access_token(
        user_id=user_id,
        username="auditor_iqbal",
        role=RoleEnum.AUDITOR
    )
    return {"Authorization": f"Bearer {token}"}
