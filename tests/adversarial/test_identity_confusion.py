"""
Adversarial Test Suite A: Identity Resolution & Confusion Attacks.
Tests A01 - A06: Verifies strict invariant that different CNICs are NEVER merged,
name transliteration works without duplication, and conflicting identity records are flagged.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from db.connection import SessionLocal
from db.models import Citizen
from services.ai.anomaly import detect_claim_anomalies
from services.ai.matcher import resolve_identity


def test_a01_identical_names_different_cnics_never_merge():
    """
    A01: Two synthetic citizens have almost identical Urdu/English names,
    same village and same family name, but different CNICs. Verify they are never merged.
    """
    citizen_a = {
        "full_name": "Muhammad Tariq Khan",
        "cnic": "42101-1111111-1",
        "village": "Bhit Shah",
        "father_name": "Abdul Ghani Khan"
    }
    citizen_b = {
        "full_name": "Mohd Tariq Khan",
        "cnic": "42101-2222222-2",
        "village": "Bhit Shah",
        "father_name": "Abdul Ghani Khan"
    }

    score, status, details = resolve_identity(citizen_a, citizen_b)

    assert score == 0.0, f"Expected 0.0 match score for different CNICs, got {score}"
    assert status == "cnic_mismatch", f"Expected cnic_mismatch status, got {status}"
    assert details.get("requires_proof") is True
    assert "Two different CNICs are never merged" in details.get("reason", "")


def test_a02_same_cnic_multiple_transliterations_normalized():
    """
    A02: Same CNIC appears with three different transliterations of the same name.
    Verify normalization works without creating duplicate citizens.
    """
    shared_cnic = "42101-3333333-3"
    transliterations = [
        "Mohd Aslam",
        "Muhammad Aslam",
        "M. Aslam"
    ]

    base_record = {"cnic": shared_cnic, "full_name": transliterations[0]}

    for variant in transliterations[1:]:
        input_record = {"cnic": shared_cnic, "full_name": variant}
        score, status, details = resolve_identity(input_record, base_record)
        assert details.get("cnic_match") is True
        assert score >= 0.85, f"Expected high similarity for transliteration '{variant}', got {score}"
        assert status in ("verified_match", "probable_variant_review")


def test_a03_cnic_single_digit_typo_never_silent_corrected():
    """
    A03: CNIC has one incorrect digit, while name, address and date of birth match.
    Verify the system does NOT silently correct identity.
    """
    registered = {
        "cnic": "42101-1234567-1",
        "full_name": "Parveen Bibi",
        "dob": "1985-05-12",
        "address": "Sector 4, Orangi Town, Karachi"
    }
    typo_input = {
        "cnic": "42101-1234567-2",  # Single digit difference
        "full_name": "Parveen Bibi",
        "dob": "1985-05-12",
        "address": "Sector 4, Orangi Town, Karachi"
    }

    score, status, details = resolve_identity(typo_input, registered)

    # Must refuse to merge or silently correct
    assert score == 0.0
    assert status == "cnic_mismatch"
    assert details.get("requires_proof") is True


def test_a04_cnic_applicant_utility_bill_mismatch_detected():
    """
    A04: CNIC belongs to applicant A, but utility bill belongs to applicant B.
    Verify the mismatch is not ignored.
    """
    applicant_a = {"full_name": "Zubair Ahmed", "cnic": "42101-5555555-5"}
    bill_owner_b = {"full_name": "Ghulam Mustafa", "cnic": "42101-7777777-7"}

    score, status, details = resolve_identity(applicant_a, bill_owner_b)

    assert score == 0.0
    assert status == "cnic_mismatch"


def test_a05_concurrent_duplicate_cnic_creation_db_uniqueness():
    """
    A05: Two requests attempt to create the same citizen with the same CNIC.
    Verify database uniqueness prevents duplicates.
    """
    session = SessionLocal()
    test_cnic = "42101-9999999-9"

    # Clean up if exists from prior test runs
    existing = session.query(Citizen).filter(Citizen.cnic == test_cnic).all()
    for e in existing:
        session.delete(e)
    session.commit()

    try:
        citizen1 = Citizen(
            cnic=test_cnic,
            full_name="Duplicate Test Citizen 1",
            phone="03001234567",
            monthly_income=20000.0
        )
        session.add(citizen1)
        session.commit()

        # Second insertion with identical CNIC must raise IntegrityError
        citizen2 = Citizen(
            cnic=test_cnic,
            full_name="Duplicate Test Citizen 2",
            phone="03007654321",
            monthly_income=22000.0
        )
        session.add(citizen2)
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        # Clean up
        session.query(Citizen).filter(Citizen.cnic == test_cnic).delete()
        session.commit()
        session.close()


def test_a06_applicant_submits_conflicting_cnics_across_sessions():
    """
    A06: Same applicant submits documents with different CNIC values in two separate sessions.
    Verify conflicting evidence is preserved and flagged.
    """
    historical = [
        {"case_id": f"CAS-OLD-{i}", "cnic": f"42101-1111111-{i}", "phone": "03001112233"}
        for i in range(1, 4)
    ]
    new_claim = {
        "case_id": "CAS-NEW-4",
        "cnic": "42101-9999999-9",  # Conflicting CNIC with same phone number
        "phone": "03001112233",
        "requested_amount": 12000.0,
        "monthly_income": 20000.0
    }

    anomaly = detect_claim_anomalies(new_claim, historical_claims=historical)

    # Must flag suspicious duplicate phone burst across different CNICs
    assert anomaly["is_anomaly"] is True
    assert "REPEAT_PHONE_BURST" in anomaly["flags"]
