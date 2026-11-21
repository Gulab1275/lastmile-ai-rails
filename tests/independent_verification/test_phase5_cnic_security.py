"""
Independent Verification Mission - Phase 5: CNIC Security Testing
Thorough verification of CNIC format validation, length checks, character sets,
Unicode normalization, database constraints, and API entry points across the Rahbar platform.

Tests:
1. Multi-endpoint API validation (cases, mock/nadra, mock/complaints, auth/register)
2. Negative test cases:
   - Incorrect lengths (10, 11, 12, 14, 16 digits)
   - Alphabetic characters (embedded, prefix, suffix, checksum letter)
   - Incorrect separators (slash, dot, underscore, space)
   - Empty string and pure whitespace
   - Null values
3. Unicode digits behavior analysis (Urdu / Arabic Eastern numerals vs ASCII regex)
4. Positive test cases:
   - 15-char standard dashed format (XXXXX-XXXXXXX-X)
   - 13-digit raw numeric format (XXXXXXXXXXXXX)
5. Database-level constraints vs Schema-level validation
"""
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from services.shared.schemas import (
    CaseCreate,
    CitizenProfile,
    ClaimCreate,
    MockNADRARequest,
    MockComplaintRequest,
    UserCreate,
    RoleEnum,
)
from db.models import Citizen
from sqlalchemy.exc import IntegrityError


# ============================================================================
# 1. Negative Test Cases - ASCII Invalid CNICs (Must raise ValidationError)
# ============================================================================

INVALID_ASCII_CNICS = [
    # Incorrect lengths
    ("4210112345", "too_short_10_digits"),
    ("42101123456", "too_short_11_digits"),
    ("42101-123456-1", "short_body_6_digits"),
    ("4210-1234567-1", "short_prefix_4_digits"),
    ("42101-1234567-", "missing_check_digit"),
    ("42101123456789", "too_long_14_digits"),
    ("4210112345678901", "too_long_16_digits"),
    ("42101-12345678-1", "long_body_8_digits"),
    ("421011-1234567-1", "long_prefix_6_digits"),

    # Alphabetic / Alphanumeric characters
    ("42101-123456A-1", "letter_in_body"),
    ("42101-1234567-X", "letter_in_checksum"),
    ("ABCDE-1234567-1", "letters_in_prefix"),
    ("42101A2345671", "letter_in_raw_13"),
    ("CNIC4210112345", "prefix_text"),

    # Incorrect separators
    ("42101/1234567/1", "slashes_separator"),
    ("42101.1234567.1", "dots_separator"),
    ("42101_1234567_1", "underscores_separator"),
    ("42101 1234567 1", "spaces_separator"),
    ("42101--1234567-1", "double_hyphen"),

    # Empty and whitespace
    ("", "empty_string"),
    ("   ", "whitespace_only"),
    (" 42101-1234567-1 ", "untrimmed_whitespace"),
    ("42101-1234567-1\n", "trailing_newline"),
]


@pytest.mark.parametrize("invalid_cnic,reason", INVALID_ASCII_CNICS)
def test_case_create_rejects_invalid_cnic(invalid_cnic: str, reason: str):
    """CaseCreate must reject invalid CNICs via regex pattern."""
    with pytest.raises(ValidationError):
        CaseCreate(
            citizen_name="Test Citizen",
            cnic=invalid_cnic,
            phone="+923001234567",
            household_size=4,
            monthly_income=25000.0,
            requested_amount=12000.0,
        )


@pytest.mark.parametrize("invalid_cnic,reason", INVALID_ASCII_CNICS)
def test_mock_nadra_request_rejects_invalid_cnic(invalid_cnic: str, reason: str):
    """MockNADRARequest must reject invalid CNICs via regex pattern."""
    with pytest.raises(ValidationError):
        MockNADRARequest(
            cnic=invalid_cnic,
            full_name="Test Citizen",
            phone="+923001234567",
        )


@pytest.mark.parametrize("invalid_cnic,reason", INVALID_ASCII_CNICS)
def test_mock_complaint_request_rejects_invalid_cnic(invalid_cnic: str, reason: str):
    """MockComplaintRequest must reject invalid CNICs via regex pattern."""
    with pytest.raises(ValidationError):
        MockComplaintRequest(
            citizen_cnic=invalid_cnic,
            category="eligibility_delay",
            description="Testing complaint submission with invalid CNIC",
        )


@pytest.mark.parametrize("invalid_cnic,reason", INVALID_ASCII_CNICS)
def test_citizen_profile_rejects_invalid_cnic(invalid_cnic: str, reason: str):
    """CitizenProfile must reject invalid CNICs via regex pattern."""
    with pytest.raises(ValidationError):
        CitizenProfile(
            cnic=invalid_cnic,
            full_name="Test Citizen",
        )


@pytest.mark.parametrize("invalid_cnic,reason", INVALID_ASCII_CNICS)
def test_claim_create_rejects_invalid_cnic(invalid_cnic: str, reason: str):
    """ClaimCreate must reject invalid CNICs via regex pattern."""
    with pytest.raises(ValidationError):
        ClaimCreate(
            citizen_cnic=invalid_cnic,
            claim_amount=12000.0,
        )


def test_cnic_rejects_null_none_values():
    """All models must reject None / null for mandatory CNIC fields."""
    with pytest.raises(ValidationError):
        CaseCreate(
            citizen_name="Test Citizen",
            cnic=None,  # type: ignore
            phone="+923001234567",
            household_size=4,
            monthly_income=25000.0,
        )
    with pytest.raises(ValidationError):
        MockNADRARequest(
            cnic=None,  # type: ignore
            full_name="Test Citizen",
        )
    with pytest.raises(ValidationError):
        MockComplaintRequest(
            citizen_cnic=None,  # type: ignore
            category="fraud_report",
            description="Null CNIC complaint",
        )


# ============================================================================
# 2. Unicode Digits Security (Strict Rejection with ASCII [0-9])
# ============================================================================

def test_cnic_unicode_digits_analysis():
    """
    Phase 2 Security Hardening:
    Replaces Unicode-sensitive \d with ASCII [0-9].
    Urdu, Arabic, and mixed Unicode numerals MUST be strictly rejected with ValidationError.
    """
    urdu_dashed = "۴۲۱۰۱-۱۲۳۴۵۶۷-۱"
    urdu_raw = "۴۲۱۰۱۱۲۳۴۵۶۷۱"
    arabic_dashed = "٤٢١٠١-١٢٣٤٥٦٧-١"
    mixed_unicode = "42101-۱۲34567-1"

    # All must raise ValidationError under strict ASCII [0-9] regex
    with pytest.raises(ValidationError):
        MockNADRARequest(cnic=urdu_dashed, full_name="Parveen Bibi")

    with pytest.raises(ValidationError):
        MockNADRARequest(cnic=urdu_raw, full_name="Parveen Bibi")

    with pytest.raises(ValidationError):
        MockNADRARequest(cnic=arabic_dashed, full_name="Parveen Bibi")

    with pytest.raises(ValidationError):
        MockNADRARequest(cnic=mixed_unicode, full_name="Parveen Bibi")

    with pytest.raises(ValidationError):
        CaseCreate(
            citizen_name="Parveen Bibi",
            cnic=urdu_dashed,
            phone="+923001234567",
            household_size=3,
            monthly_income=15000.0,
        )


# ============================================================================
# 3. Positive Test Cases - Dual Standard Support
# ============================================================================

VALID_CNICS = [
    ("42101-1234567-1", "standard_dashed_sindh"),
    ("35201-7654321-2", "standard_dashed_punjab"),
    ("17301-9998887-3", "standard_dashed_kpk"),
    ("54400-1122334-4", "standard_dashed_balochistan"),
    ("61101-3344556-5", "standard_dashed_islamabad"),
    ("4210112345671", "raw_numeric_13_digits"),
    ("3520176543212", "raw_numeric_punjab_13"),
    ("1730199988873", "raw_numeric_kpk_13"),
]


@pytest.mark.parametrize("valid_cnic,desc", VALID_CNICS)
def test_pydantic_accepts_valid_dashed_and_13digit_cnics(valid_cnic: str, desc: str):
    """Confirm both dashed (15-char) and unhyphenated (13-digit) formats are accepted."""
    c = CaseCreate(
        citizen_name="Valid Citizen",
        cnic=valid_cnic,
        phone="+923001234567",
        household_size=3,
        monthly_income=18000.0,
        requested_amount=12000.0,
    )
    assert c.cnic == valid_cnic

    req = MockNADRARequest(
        cnic=valid_cnic,
        full_name="Valid Citizen",
    )
    assert req.cnic == valid_cnic


# ============================================================================
# 4. HTTP API Endpoint Tests via TestClient
# ============================================================================

def test_api_cases_endpoint_rejects_malformed_cnic(client: TestClient, citizen_headers: dict):
    """POST /api/v1/cases with invalid CNIC must return HTTP 422 Unprocessable Entity."""
    payload = {
        "citizen_name": "Test Citizen",
        "cnic": "42101-12345-X",  # Invalid checksum letter and length
        "phone": "+923001234567",
        "household_size": 3,
        "monthly_income": 15000.0,
        "requested_amount": 10000.0,
    }
    response = client.post("/api/v1/cases", json=payload, headers=citizen_headers)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("cnic" in str(err.get("loc", [])) for err in errors)


def test_api_cases_endpoint_accepts_valid_dashed_cnic(client: TestClient, citizen_headers: dict):
    """POST /api/v1/cases with valid dashed CNIC must succeed (201 Created)."""
    payload = {
        "citizen_name": "Parveen Bibi",
        "cnic": "42101-1234567-1",
        "phone": "+923001234567",
        "household_size": 3,
        "monthly_income": 15000.0,
        "requested_amount": 10000.0,
    }
    response = client.post("/api/v1/cases", json=payload, headers=citizen_headers)
    assert response.status_code == 201
    assert response.json()["cnic"] == "42101-1234567-1"


def test_api_cases_endpoint_accepts_valid_13digit_cnic(client: TestClient, citizen_headers: dict):
    """POST /api/v1/cases with valid 13-digit unhyphenated CNIC must succeed (201 Created)."""
    payload = {
        "citizen_name": "Parveen Bibi",
        "cnic": "4210112345671",
        "phone": "+923001234567",
        "household_size": 3,
        "monthly_income": 15000.0,
        "requested_amount": 10000.0,
    }
    response = client.post("/api/v1/cases", json=payload, headers=citizen_headers)
    assert response.status_code == 201
    assert response.json()["cnic"] == "4210112345671"


def test_api_mock_nadra_endpoint_cnic_validation(client: TestClient):
    """POST /api/v1/mock/identity/verify validates CNIC via Pydantic schema."""
    # 1. Invalid length returns 422
    bad_resp = client.post("/api/v1/mock/identity/verify", json={
        "cnic": "12345",
        "full_name": "Farooq Ahmed"
    })
    assert bad_resp.status_code == 422

    # 2. Slashes instead of dashes returns 422
    slash_resp = client.post("/api/v1/mock/identity/verify", json={
        "cnic": "42101/1234567/1",
        "full_name": "Farooq Ahmed"
    })
    assert slash_resp.status_code == 422

    # 3. Valid dashed format returns 200
    good_resp = client.post("/api/v1/mock/identity/verify", json={
        "cnic": "42101-1234567-1",
        "full_name": "Parveen Bibi"
    })
    assert good_resp.status_code == 200
    assert good_resp.json()["matched"] is True

    # 4. Valid 13-digit format returns 200
    raw_resp = client.post("/api/v1/mock/identity/verify", json={
        "cnic": "4210112345671",
        "full_name": "Parveen Bibi"
    })
    assert raw_resp.status_code == 200
    assert raw_resp.json()["matched"] is True


def test_api_mock_complaints_endpoint_cnic_validation(client: TestClient):
    """POST /api/v1/mock/complaints validates citizen_cnic."""
    # 1. Letters in CNIC returns 422
    bad_resp = client.post("/api/v1/mock/complaints", json={
        "citizen_cnic": "42101-123456A-1",
        "phone": "+923001234567",
        "category": "delay",
        "description": "Payment delayed for one month"
    })
    assert bad_resp.status_code == 422

    # 2. Valid CNIC returns 200
    good_resp = client.post("/api/v1/mock/complaints", json={
        "citizen_cnic": "42101-1234567-1",
        "phone": "+923001234567",
        "category": "delay",
        "description": "Payment delayed for one month"
    })
    assert good_resp.status_code == 200
    assert good_resp.json()["status"] == "LOGGED"


def test_api_auth_register_cnic_validation(client: TestClient):
    """POST /api/v1/auth/register validates optional cnic field."""
    # 1. Invalid CNIC format returns 422
    bad_resp = client.post("/api/v1/auth/register", json={
        "username": "new_citizen_invalid",
        "full_name": "New Citizen",
        "role": "citizen",
        "password": "Password123!",
        "cnic": "INVALID-CNIC-HERE"
    })
    assert bad_resp.status_code == 422

    # 2. Valid CNIC format succeeds
    good_resp = client.post("/api/v1/auth/register", json={
        "username": "new_citizen_valid_cnic",
        "full_name": "New Citizen",
        "role": "citizen",
        "password": "Password123!",
        "cnic": "42101-9988776-5"
    })
    assert good_resp.status_code == 201
    assert good_resp.json()["cnic"] == "42101-9988776-5"


# ============================================================================
# 5. Database-Level Enforcement vs Schema Enforcement
# ============================================================================

def test_database_model_cnic_column_constraints():
    """
    Verify SQLAlchemy Citizen table column specifications:
    - String(15) length limit
    - unique=True constraint
    - nullable=False constraint
    - CheckConstraint enforces ASCII format (5-7-1 or 13 digits)
    """
    col = Citizen.__table__.columns["cnic"]
    assert col.nullable is False
    assert col.type.length == 15
    assert col.unique is True or any(idx.unique for idx in Citizen.__table__.indexes if "cnic" in [c.name for c in idx.columns])

    # Verify CheckConstraint in model table_args
    check_constraints = [c for c in Citizen.__table__.constraints if hasattr(c, "sqltext")]
    assert any("check_valid_cnic_format" in getattr(c, "name", "") for c in check_constraints)


def test_database_check_constraint_rejects_invalid_cnic():
    """Verify live PostgreSQL rejects direct SQL insert of invalid CNIC."""
    from db.connection import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        # 1. Invalid CNIC with letter must raise CheckViolation
        with pytest.raises(Exception) as exc_info:
            conn.execute(text("""
                INSERT INTO citizens (id, cnic, full_name, household_size, monthly_income)
                VALUES ('test_bad_cnic_probe_99', '42101-123456A-1', 'Bad CNIC Probe', 1, 0);
            """))
            conn.commit()
        assert "check_valid_cnic_format" in str(exc_info.value) or "CheckViolation" in str(exc_info.value)
        conn.rollback()

        # 2. Valid CNIC succeeds
        conn.execute(text("""
            INSERT INTO citizens (id, cnic, full_name, household_size, monthly_income)
            VALUES ('test_good_cnic_probe_99', '42101-7777777-1', 'Good CNIC Probe', 1, 0);
        """))
        conn.commit()
        conn.execute(text("DELETE FROM citizens WHERE id = 'test_good_cnic_probe_99';"))
        conn.commit()
