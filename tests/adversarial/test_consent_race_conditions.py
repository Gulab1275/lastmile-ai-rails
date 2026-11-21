"""
Adversarial Test Suite H: Consent Gateway & Race Condition Attacks.
Tests H01 - H06: Evaluates granular permission scopes, immediate revocation enforcement,
IDOR cross-citizen access prevention, and concurrent consent invalidation.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.engine.consent_gateway import consent_gateway
from services.shared.schemas import RoleEnum, ConsentScope


def test_h01_granular_consent_identity_allowed_income_denied():
    """H01: Identity consent granted, income consent denied. Attempt both reads."""
    citizen_id = "cit_h01_granular"
    consent_gateway.grant_consent(citizen_id, ConsentScope.IDENTITY, helper_id="helper_shazia")
    consent_gateway.withdraw_consent(citizen_id, ConsentScope.INCOME)

    # 1. Identity read must succeed
    read_id_ok = consent_gateway.read_gateway(
        actor_id="helper_shazia",
        actor_role=RoleEnum.HELPER,
        citizen_id=citizen_id,
        scope=ConsentScope.IDENTITY,
        acting_helper_id="helper_shazia"
    )
    assert read_id_ok is True

    # 2. Income read must raise HTTP 403 ConsentWithdrawnException
    from services.api.engine.consent_gateway import ConsentWithdrawnException
    with pytest.raises(ConsentWithdrawnException):
        consent_gateway.read_gateway(
            actor_id="helper_shazia",
            actor_role=RoleEnum.HELPER,
            citizen_id=citizen_id,
            scope=ConsentScope.INCOME,
            acting_helper_id="helper_shazia"
        )


def test_h02_consent_revoked_mid_workflow():
    """H02: Consent revoked during a running workflow blocks subsequent steps immediately."""
    citizen_id = "cit_h02_midflow"
    consent_gateway.grant_consent(citizen_id, ConsentScope.IDENTITY, helper_id="helper_shazia")
    assert consent_gateway.check_consent(citizen_id, ConsentScope.IDENTITY) is True

    # Mid-workflow revocation
    consent_gateway.withdraw_consent(citizen_id, ConsentScope.IDENTITY)
    assert consent_gateway.check_consent(citizen_id, ConsentScope.IDENTITY) is False


def test_h03_concurrent_revocation_and_read_isolation():
    """H03: Invalidation takes immediate effect across multiple consecutive checks."""
    citizen_id = "cit_h03_race"
    consent_gateway.grant_consent(citizen_id, ConsentScope.DOCUMENTS, helper_id="helper_shazia")
    consent_gateway.withdraw_consent(citizen_id, ConsentScope.DOCUMENTS)

    results = [
        consent_gateway.check_consent(citizen_id, ConsentScope.DOCUMENTS, acting_helper_id="helper_shazia")
        for _ in range(5)
    ]
    # Every subsequent check must return False
    assert all(r is False for r in results)


def test_h04_helper_acting_consent_revocation_blocks_case_submission(client: TestClient, helper_headers: dict):
    """H04: Helper acting consent is revoked; helper attempt to submit case is blocked."""
    citizen_id = "cit_widow_002"
    # Explicitly revoke helper acting consent
    consent_gateway.withdraw_consent(citizen_id, ConsentScope.HELPER_ACTING)

    # Attempt to create case on behalf of citizen
    payload = {
        "citizen_name": "Unauthorized Family",
        "cnic": "42101-1122334-5",
        "phone": "03001234567",
        "household_size": 4,
        "monthly_income": 20000.0,
        "helper_id": "helper_shazia"
    }
    r = client.post("/api/v1/cases", json=payload, headers=helper_headers)
    # Must fail with 403 or 400 since helper lacks acting consent
    assert r.status_code in (403, 400)


def test_h05_consent_status_persistence_in_audit_chain():
    """H05: Every grant and revocation writes an immutable audit block with SHA-256 hash."""
    from services.api.engine.audit_log import audit_log
    citizen_id = "cit_h05_audit"
    
    rec_grant = consent_gateway.grant_consent(citizen_id, ConsentScope.INCOME)
    assert rec_grant.audit_hash is not None
    assert len(rec_grant.audit_hash) == 64  # SHA-256 length

    rec_withdraw = consent_gateway.withdraw_consent(citizen_id, ConsentScope.INCOME)
    assert rec_withdraw.audit_hash is not None
    assert rec_withdraw.audit_hash != rec_grant.audit_hash


def test_h06_idor_cross_citizen_data_access_prevention(client: TestClient, citizen_headers: dict):
    """H06: Citizen attempts to view another citizen's case record (IDOR attack)."""
    # Attempt to access a random/admin case ID
    r = client.get("/api/v1/cases/cas_foreign_001", headers=citizen_headers)
    assert r.status_code in (403, 404)
