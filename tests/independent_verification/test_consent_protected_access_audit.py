"""
Task 3 Independent Verification Test Suite:
Audits all consent-protected access paths across the Rahbar backend.
Verifies that helpers cannot access, view, modify, evaluate, explain, or sync citizen data
without active point-of-use consent.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.engine.consent_gateway import consent_gateway
from services.api.routes.cases import _CASES_DB
from services.api.security.auth import _USERS_BY_USERNAME
from services.shared.schemas import CaseResponse, CaseStatus, ConsentScope, DocumentAttachment, RoleEnum
from services.ai.sync import process_offline_sync_batch


@pytest.fixture
def test_case_setup():
    """Sets up a test case assigned to helper_shazia for citizen_parveen."""
    cit_id = _USERS_BY_USERNAME["citizen_parveen"]
    helper_id = _USERS_BY_USERNAME["helper_shazia"]
    case_id = f"cas_audit_{uuid.uuid4().hex[:8]}"

    from datetime import datetime
    now = datetime.utcnow()
    case_obj = CaseResponse(
        id=case_id,
        citizen_id=cit_id,
        citizen_name="Parveen Bibi",
        cnic="42101-1234567-1",
        phone="0300-1234567",
        household_size=4,
        monthly_income=22000.0,
        benefit_type="relief_cash_grant",
        requested_amount=12000.0,
        status=CaseStatus.DRAFT,
        helper_id=helper_id,
        documents=[],
        created_at=now,
        updated_at=now
    )
    _CASES_DB[case_id] = case_obj
    return case_id, cit_id, helper_id


def test_helper_list_cases_consent_filtering(client: TestClient, helper_headers: dict, citizen_headers: dict, test_case_setup):
    """
    Test that GET /api/v1/cases strictly excludes cases when HELPER_ACTING consent is missing or revoked.
    """
    case_id, cit_id, helper_id = test_case_setup

    # 1. Grant consent: case must appear
    consent_gateway.grant_consent(
        citizen_id=cit_id,
        scope=ConsentScope.HELPER_ACTING,
        helper_id=helper_id,
        actor_id=cit_id,
        actor_role=RoleEnum.CITIZEN
    )
    res = client.get("/api/v1/cases", headers=helper_headers)
    assert res.status_code == 200
    case_ids = [c["id"] for c in res.json()]
    assert case_id in case_ids, "Case should be visible to helper when active consent exists"

    # 2. Revoke consent: case must be omitted from helper view
    consent_gateway.withdraw_consent(
        citizen_id=cit_id,
        scope=ConsentScope.HELPER_ACTING,
        actor_id=cit_id,
        actor_role=RoleEnum.CITIZEN
    )
    res_revoked = client.get("/api/v1/cases", headers=helper_headers)
    assert res_revoked.status_code == 200
    revoked_case_ids = [c["id"] for c in res_revoked.json()]
    assert case_id not in revoked_case_ids, "Case must NOT be visible to helper after consent is revoked"


def test_helper_get_case_blocked_on_revocation(client: TestClient, helper_headers: dict, test_case_setup):
    """
    Test that GET /api/v1/cases/{id} returns HTTP 403 when helper consent is withdrawn.
    """
    case_id, cit_id, helper_id = test_case_setup

    # Grant consent
    consent_gateway.grant_consent(cit_id, ConsentScope.HELPER_ACTING, helper_id=helper_id)
    consent_gateway.grant_consent(cit_id, ConsentScope.IDENTITY, helper_id=helper_id)
    res = client.get(f"/api/v1/cases/{case_id}", headers=helper_headers)
    assert res.status_code == 200

    # Revoke consent
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)
    res_blocked = client.get(f"/api/v1/cases/{case_id}", headers=helper_headers)
    assert res_blocked.status_code == 403, "Direct read must be blocked with HTTP 403 upon revocation"


def test_helper_attach_document_blocked_on_revocation(client: TestClient, helper_headers: dict, test_case_setup):
    """
    Test that POST /api/v1/cases/{id}/documents returns HTTP 403 when helper consent is withdrawn.
    """
    case_id, cit_id, helper_id = test_case_setup
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)

    doc_payload = {
        "doc_id": "doc_audit_101",
        "doc_type": "utility_bill",
        "file_name": "utility_bill.jpg",
        "file_url": "https://storage.local/utility_bill.jpg",
        "ocr_confidence": 0.92,
        "is_blurry": False,
        "is_tampered": False
    }
    res = client.post(f"/api/v1/cases/{case_id}/documents", json=doc_payload, headers=helper_headers)
    assert res.status_code == 403, "Document attachment must fail closed when helper consent is withdrawn"


def test_helper_submit_case_blocked_on_revocation(client: TestClient, helper_headers: dict, test_case_setup):
    """
    Test that POST /api/v1/cases/{id}/submit returns HTTP 403 when helper consent is withdrawn.
    """
    case_id, cit_id, helper_id = test_case_setup
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)

    res = client.post(f"/api/v1/cases/{case_id}/submit", headers=helper_headers)
    assert res.status_code == 403, "Case submission must fail closed when helper consent is withdrawn"


def test_helper_evaluate_case_blocked_on_revocation(client: TestClient, helper_headers: dict, test_case_setup):
    """
    Test that POST /api/v1/decisions/evaluate/{id} returns HTTP 403 when helper consent is withdrawn.
    """
    case_id, cit_id, helper_id = test_case_setup
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)

    res = client.post(f"/api/v1/decisions/evaluate/{case_id}", headers=helper_headers)
    assert res.status_code == 403, "Decision evaluation must fail closed when helper consent is withdrawn"


def test_helper_explain_decision_blocked_on_revocation(client: TestClient, helper_headers: dict, officer_headers: dict, test_case_setup):
    """
    Test that GET /api/v1/decisions/explain/{id} returns HTTP 403 when helper consent is withdrawn.
    """
    case_id, cit_id, helper_id = test_case_setup

    # Temporarily evaluate as officer to generate decision
    res_eval = client.post(f"/api/v1/decisions/evaluate/{case_id}", headers=officer_headers)
    assert res_eval.status_code == 200

    # Revoke helper consent
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)

    res_explain = client.get(f"/api/v1/decisions/explain/{case_id}", headers=helper_headers)
    assert res_explain.status_code == 403, "Decision explanation must fail closed when helper consent is withdrawn"


def test_offline_sync_blocked_when_consent_revoked():
    """
    Test that process_offline_sync_batch flags items with SYNC_FAILED_CONSENT_REVOKED
    if helper consent has been withdrawn.
    """
    cit_id = f"cit_offline_{uuid.uuid4().hex[:6]}"
    helper_id = "helper_test_sync"

    # Revoke consent explicitly in database
    consent_gateway.withdraw_consent(cit_id, ConsentScope.HELPER_ACTING)

    queued = [{
        "idempotency_key": f"key_{uuid.uuid4().hex[:8]}",
        "citizen_id": cit_id,
        "citizen_data": {
            "name": "Offline Citizen",
            "cnic": "42101-9988776-1",
            "monthly_income": 20000.0,
            "household_size": 4
        }
    }]

    batch_res = process_offline_sync_batch(
        helper_id=helper_id,
        batch_id="batch_revoked_01",
        queued_cases=queued
    )

    assert batch_res["summary"]["failed_count"] == 1
    assert batch_res["items"][0]["status"] == "SYNC_FAILED_CONSENT_REVOKED"
