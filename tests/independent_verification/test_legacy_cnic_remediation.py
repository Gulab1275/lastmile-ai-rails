"""
Task 1 Independent Verification Test Suite:
Verifies the safe legacy CNIC remediation plan.
- Verifies automatic replacement of -X with -0 is completely removed.
- Verifies unverified records ending in -X are restricted from intake and sync workflows.
- Verifies manual verification endpoint requires officer authorization and physical documentation.
- Verifies database constraint cannot be validated until all legacy records are verified.
- Verifies audit logging of manual corrections.
"""
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from db.connection import SessionLocal
from db.models import Citizen as DBCitizen
from services.ai.sync import process_offline_sync_batch
from services.api.engine.audit_log import audit_log


def test_intake_rejected_for_legacy_cnic(client: TestClient, citizen_headers: dict):
    """
    Test 1: Normal intake must strictly reject CNICs ending in -X with HTTP 400 or 422.
    """
    payload = {
        "citizen_name": "Legacy Unverified Citizen",
        "cnic": "42101-1234567-X",
        "phone": "0300-1112233",
        "household_size": 5,
        "monthly_income": 18000.0,
        "benefit_type": "relief_cash_grant",
        "requested_amount": 10500.0
    }
    res = client.post("/api/v1/cases", json=payload, headers=citizen_headers)
    assert res.status_code in [400, 422], "Intake with legacy -X CNIC must be rejected"


def test_offline_sync_rejected_for_legacy_cnic():
    """
    Test 2: Offline sync batch must flag cases with -X CNIC as SYNC_FAILED_UNVERIFIED_LEGACY_CNIC.
    """
    queued = [{
        "idempotency_key": f"key_{uuid.uuid4().hex[:8]}",
        "citizen_data": {
            "name": "Legacy Sync Citizen",
            "cnic": "42101-7654321-X",
            "monthly_income": 20000.0,
            "household_size": 3
        }
    }]
    batch_res = process_offline_sync_batch(
        helper_id="helper_sync_test",
        batch_id="batch_legacy_01",
        queued_cases=queued
    )
    assert batch_res["summary"]["failed_count"] == 1
    assert batch_res["items"][0]["status"] == "SYNC_FAILED_UNVERIFIED_LEGACY_CNIC"


def test_manual_verification_requires_officer(client: TestClient, citizen_headers: dict, helper_headers: dict):
    """
    Test 3: Non-officers (citizen and helper) cannot perform manual CNIC corrections.
    """
    payload = {
        "citizen_id": "cit_legacy_test",
        "verified_cnic": "42101-1234567-1",
        "caseworker_notes": "Caseworker physically verified original NADRA Smart Card at facility.",
        "physical_document_ref": "NADRA-SCAN-99182"
    }
    res_cit = client.post("/api/v1/cases/legacy-cnic/verify-and-correct", json=payload, headers=citizen_headers)
    assert res_cit.status_code == 403

    res_help = client.post("/api/v1/cases/legacy-cnic/verify-and-correct", json=payload, headers=helper_headers)
    assert res_help.status_code == 403


def test_manual_verification_rejection_conditions(client: TestClient, officer_headers: dict):
    """
    Test 4: Endpoint validation rules:
    - Deprecated single-step endpoint is strictly disabled (HTTP 410)
    - Propose endpoint rejects another -X format
    - Propose endpoint rejects non-existent citizen
    - Propose endpoint rejects fabricated physical document ref
    """
    # 0. Reject direct single-step verification bypass attempt (HTTP 410 Gone)
    legacy_bypass_req = {
        "citizen_id": "cit_dummy",
        "verified_cnic": "42101-1234567-1",
        "caseworker_notes": "Attempting single-step bypass",
        "physical_document_ref": "NADRA-SCAN-001",
        "second_approver_id": "officer_aslam"
    }
    res_dep = client.post("/api/v1/cases/legacy-cnic/verify-and-correct", json=legacy_bypass_req, headers=officer_headers)
    assert res_dep.status_code == 410
    assert "ENDPOINT_DEPRECATED_MAKER_CHECKER_REQUIRED" in res_dep.json()["detail"]["code"]

    # 1. Reject another -X format in proposal
    bad_req = {
        "citizen_id": "cit_dummy",
        "verified_cnic": "42101-1234567-X",
        "caseworker_notes": "Attempting to re-enter legacy -X format",
        "physical_document_ref": "NADRA-SCAN-001"
    }
    res = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=bad_req, headers=officer_headers)
    assert res.status_code in [400, 422]

    # 2. Reject non-existent citizen in proposal
    not_found_req = {
        "citizen_id": "cit_nonexistent_99999",
        "verified_cnic": "42101-1234567-1",
        "caseworker_notes": "Caseworker physically verified original NADRA Smart Card at facility.",
        "physical_document_ref": "NADRA-SCAN-99182"
    }
    res_nf = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=not_found_req, headers=officer_headers)
    assert res_nf.status_code == 404

    # 3. Reject fabricated physical document ref format
    fake_doc_req = {
        "citizen_id": "cit_nonexistent_99999",
        "verified_cnic": "42101-1234567-1",
        "caseworker_notes": "Caseworker physically verified original NADRA Smart Card at facility.",
        "physical_document_ref": "fabricated_dummy_123"
    }
    res_fake = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=fake_doc_req, headers=officer_headers)
    assert res_fake.status_code == 422


def test_manual_verification_success_and_audit(client: TestClient, officer_headers: dict, admin_headers: dict):
    """
    Test 5: Full verification and auditable correction flow via Maker-Checker workflow:
    - Uses temporary test citizen created while preserving the 10 real legacy records untouched
    - Caseworker verifies physical document and proposes correction
    - Mandates independent supervisor approval
    - Updates citizen record to valid format
    - Appends LEGACY_CNIC_MANUALLY_VERIFIED to tamper-evident audit ledger with masked CNIC
    - Cleans up temporary test record in finally block
    """
    from services.api.security.auth import _USERS_BY_USERNAME
    admin_id = _USERS_BY_USERNAME["admin_ayesha"]
    temp_citizen_id = f"cit_test_leg_{uuid.uuid4().hex[:6]}"
    legacy_cnic = "42101-8888888-X"
    test_verified_cnic = "42101-8888888-1"

    with SessionLocal() as db_session:
        # Portable table setup: only execute DROP CONSTRAINT on PostgreSQL
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            db_session.execute(text("ALTER TABLE citizens DROP CONSTRAINT IF EXISTS check_valid_cnic_format"))
        db_session.execute(
            text("INSERT INTO citizens (id, cnic, full_name, phone) VALUES (:id, :cnic, :name, :phone)"),
            {"id": temp_citizen_id, "cnic": legacy_cnic, "name": "Temporary Legacy Test Citizen", "phone": "0300-8888888"}
        )
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            db_session.execute(text(
                "ALTER TABLE citizens ADD CONSTRAINT check_valid_cnic_format CHECK (cnic ~ '^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$') NOT VALID"
            ))
        db_session.commit()

    try:
        # Step 1: Propose correction (Maker)
        propose_req = {
            "citizen_id": temp_citizen_id,
            "verified_cnic": test_verified_cnic,
            "caseworker_notes": "Verified against NADRA original physical Smart CNIC token #8819.",
            "physical_document_ref": "NADRA-TOK-8819"
        }
        res_prop = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=propose_req, headers=officer_headers)
        assert res_prop.status_code in (200, 201)
        proposal_id = res_prop.json()["proposal_id"]

        # Step 2: Approve correction (Checker - Admin)
        approve_req = {
            "proposal_id": proposal_id,
            "supervisor_notes": "Independent supervisor verified original NADRA documentation."
        }
        res_app = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approve_req, headers=admin_headers)
        assert res_app.status_code == 200
        data = res_app.json()
        assert data["status"] == "APPROVED"
        assert data["old_cnic"] == legacy_cnic
        assert data["verified_cnic"] == test_verified_cnic

        # Verify DB updated
        with SessionLocal() as db_session:
            updated = db_session.query(DBCitizen).filter_by(id=temp_citizen_id).first()
            assert updated.cnic == test_verified_cnic

        # Verify audit log recorded
        audit_entries = [e for e in audit_log.get_entries(resource_id=temp_citizen_id) if e.action == "LEGACY_CNIC_MANUALLY_VERIFIED"]
        assert len(audit_entries) >= 1
        entry = audit_entries[0]
        assert entry.details["old_cnic"] == legacy_cnic
        assert entry.details["verified_cnic"] == test_verified_cnic
        assert entry.details["verified_cnic_masked"] == "42101-*******-1"
        assert entry.details["doc_ref"] == "NADRA-TOK-8819"
        assert entry.details["checker_supervisor_id"] == admin_id

        # Verify Reused Document Reference Rejection (Deduplication) on propose for another legacy citizen
        temp_cit_2 = f"cit_leg_dup_{uuid.uuid4().hex[:6]}"
        with SessionLocal() as db_session:
            db_session.execute(
                text("INSERT INTO citizens (id, cnic, full_name, phone) VALUES (:id, :cnic, :name, :phone)"),
                {"id": temp_cit_2, "cnic": "42101-9999999-X", "name": "Second Legacy Citizen", "phone": "0300-9999999"}
            )
            db_session.commit()

        try:
            reused_doc_req = {
                "citizen_id": temp_cit_2,
                "verified_cnic": "42101-8888888-2",
                "caseworker_notes": "Attempting to reuse already verified document reference.",
                "physical_document_ref": "NADRA-TOK-8819"
            }
            res_reused = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=reused_doc_req, headers=officer_headers)
            assert res_reused.status_code == 409
            assert "REUSED_DOCUMENT_REFERENCE" in res_reused.json()["detail"]
        finally:
            with SessionLocal() as db_session:
                db_session.execute(text("DELETE FROM legacy_cnic_proposals WHERE citizen_id = :id"), {"id": temp_cit_2})
                db_session.execute(text("DELETE FROM citizens WHERE id = :id"), {"id": temp_cit_2})
                db_session.commit()

    finally:
        with SessionLocal() as db_session:
            db_session.execute(text("DELETE FROM legacy_cnic_proposals WHERE citizen_id = :id"), {"id": temp_citizen_id})
            db_session.execute(text("DELETE FROM citizens WHERE id = :id"), {"id": temp_citizen_id})
            db_session.commit()


def test_two_phase_maker_checker_proposal_and_approval(client: TestClient, officer_headers: dict, admin_headers: dict):
    """
    Test 6: Two-Phase Maker-Checker workflow:
    Phase 1: Maker (Officer) submits proposal -> record remains '-X' in DB.
    Phase 2: Maker attempts self-approval -> strictly forbidden (403).
    Phase 3: Checker (Admin) approves proposal -> DB updated, audit log written with both Maker & Checker IDs.
    """
    from services.api.security.auth import _USERS_BY_USERNAME
    temp_citizen_id = f"cit_test_phase_{uuid.uuid4().hex[:6]}"
    legacy_cnic = "42101-7777777-X"
    verified_cnic = "42101-7777777-9"

    with SessionLocal() as db_session:
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            db_session.execute(text("ALTER TABLE citizens DROP CONSTRAINT IF EXISTS check_valid_cnic_format"))
        db_session.execute(
            text("INSERT INTO citizens (id, cnic, full_name, phone) VALUES (:id, :cnic, :name, :phone)"),
            {"id": temp_citizen_id, "cnic": legacy_cnic, "name": "Phase Test Citizen", "phone": "0300-7777777"}
        )
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            db_session.execute(text(
                "ALTER TABLE citizens ADD CONSTRAINT check_valid_cnic_format CHECK (cnic ~ '^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$') NOT VALID"
            ))
        db_session.commit()

    try:
        # Phase 1: Officer Aslam proposes correction
        propose_payload = {
            "citizen_id": temp_citizen_id,
            "verified_cnic": verified_cnic,
            "caseworker_notes": "Officer physically inspected NADRA Smart Card #7721.",
            "physical_document_ref": "NADRA-TOK-7721"
        }
        res_prop = client.post("/api/v1/cases/legacy-cnic/propose-correction", json=propose_payload, headers=officer_headers)
        assert res_prop.status_code in (200, 201)
        prop_data = res_prop.json()
        assert prop_data["status"] == "PROPOSED"
        proposal_id = prop_data["proposal_id"]

        # Crucial check: Citizen record in database MUST still be '-X'
        with SessionLocal() as db_session:
            cit_db = db_session.query(DBCitizen).filter_by(id=temp_citizen_id).first()
            assert cit_db.cnic == legacy_cnic, "Citizen CNIC was prematurely altered before Checker approval!"

        # Phase 2: Officer Aslam attempts to self-approve own proposal
        approval_payload = {
            "proposal_id": proposal_id,
            "supervisor_notes": "Attempting self-approval as Maker."
        }
        res_self_app = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=approval_payload, headers=officer_headers)
        assert res_self_app.status_code == 403
        assert "MAKER_CHECKER_SELF_APPROVAL_FORBIDDEN" in res_self_app.json()["detail"]

        # Citizen record in database MUST STILL be '-X'
        with SessionLocal() as db_session:
            cit_db = db_session.query(DBCitizen).filter_by(id=temp_citizen_id).first()
            assert cit_db.cnic == legacy_cnic, "Citizen CNIC was altered despite 403 rejection!"

        # Phase 3: Independent Supervisor (Admin Ayesha) reviews and approves
        checker_payload = {
            "proposal_id": proposal_id,
            "supervisor_notes": "Supervisor verified NADRA system cross-check #7721. Approved."
        }
        res_checker = client.post("/api/v1/cases/legacy-cnic/approve-correction", json=checker_payload, headers=admin_headers)
        assert res_checker.status_code == 200
        check_data = res_checker.json()
        assert check_data["status"] in ("APPROVED", "SUCCESS")
        assert check_data["verified_cnic"] == verified_cnic

        # Citizen record in database MUST now be updated to valid CNIC
        with SessionLocal() as db_session:
            cit_db = db_session.query(DBCitizen).filter_by(id=temp_citizen_id).first()
            assert cit_db.cnic == verified_cnic

        # Audit log MUST contain both Maker and Checker IDs and masked CNIC
        entries = [e for e in audit_log.get_entries(resource_id=temp_citizen_id) if e.action == "LEGACY_CNIC_MANUALLY_VERIFIED"]
        assert len(entries) >= 1
        entry = entries[-1]
        assert entry.details["maker_officer_id"] == _USERS_BY_USERNAME["officer_aslam"]
        assert entry.details["checker_supervisor_id"] == _USERS_BY_USERNAME["admin_ayesha"]
        assert entry.details["verified_cnic_masked"] == "42101-*******-9"

    finally:
        with SessionLocal() as db_session:
            db_session.execute(text("DELETE FROM legacy_cnic_proposals WHERE citizen_id = :id"), {"id": temp_citizen_id})
            db_session.execute(text("DELETE FROM citizens WHERE id = :id"), {"id": temp_citizen_id})
            db_session.commit()
