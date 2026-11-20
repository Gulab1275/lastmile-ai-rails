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
import sys

# Ensure repository root is on sys.path for test discovery in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.security.auth import _USERS_BY_USERNAME, create_access_token
from services.shared.schemas import RoleEnum


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
