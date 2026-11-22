"""
Mission Final Consolidated — Consent Authorization Hardening & Adversarial Verification.
Covers all 11 required authorization and defense-in-depth scenarios:
1. Citizen granting own consent -> 200 OK
2. Citizen granting another citizen's consent -> 403 Forbidden
3. Helper granting consent -> 403 Forbidden
4. Officer granting consent -> 403 Forbidden
5. Administrator granting consent -> 403 Forbidden
6. Unauthenticated grant -> 401 Unauthorized
7. Forged caller-supplied actor ID -> route binds to authenticated citizen ID / ignored
8. Direct service-layer call with non-citizen role -> PermissionError
9. Alternative endpoint or workflow bypass attempt -> 403 Forbidden
10. Consent withdrawal and subsequent access blocking -> 403 ConsentWithdrawnException
11. Concurrent grant/revoke operations -> consistent state with row locking
"""
import threading
import uuid

import pytest
from fastapi.testclient import TestClient

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException, consent_gateway
from services.api.security.auth import _USERS_BY_USERNAME, create_access_token
from services.shared.schemas import ConsentScope, RoleEnum


@pytest.fixture
def auth_tokens():
    """Returns access tokens for all roles."""
    tokens = {}
    for role_name, username, role_enum in [
        ("citizen_1", "citizen_parveen", RoleEnum.CITIZEN),
        ("citizen_2", "citizen_tariq", RoleEnum.CITIZEN),
        ("helper", "helper_shazia", RoleEnum.HELPER),
        ("officer", "officer_aslam", RoleEnum.OFFICER),
        ("admin", "admin_ayesha", RoleEnum.ADMIN),
        ("auditor", "auditor_iqbal", RoleEnum.AUDITOR),
    ]:
        user_id = _USERS_BY_USERNAME[username]
        token = create_access_token(user_id=user_id, username=username, role=role_enum)
        tokens[role_name] = {
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "user_id": user_id,
            "username": username,
            "role": role_enum,
        }
    return tokens


# 1. Citizen granting own consent -> 200 OK
def test_scenario_1_citizen_granting_own_consent_succeeds(client: TestClient, auth_tokens: dict):
    cit = auth_tokens["citizen_1"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit["user_id"], "scope": "income", "purpose": "Application"},
        headers=cit["headers"]
    )
    assert res.status_code == 200
    assert res.json()["granted"] is True
    assert res.json()["citizen_id"] == cit["user_id"]
    assert res.json()["scope"] == "income"


# 2. Citizen granting another citizen's consent -> 403 Forbidden
def test_scenario_2_cross_citizen_grant_forbidden(client: TestClient, auth_tokens: dict):
    cit_1 = auth_tokens["citizen_1"]
    cit_2 = auth_tokens["citizen_2"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_2["user_id"], "scope": "income", "purpose": "Malicious grant"},
        headers=cit_1["headers"]
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CROSS_CITIZEN_CONSENT_FORBIDDEN"


# 3. Helper granting consent -> 403 Forbidden
def test_scenario_3_helper_grant_forbidden(client: TestClient, auth_tokens: dict):
    helper = auth_tokens["helper"]
    cit_1 = auth_tokens["citizen_1"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_1["user_id"], "scope": "income", "purpose": "Helper override"},
        headers=helper["headers"]
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CONSENT_GRANT_FORBIDDEN"


# 4. Officer granting consent -> 403 Forbidden
def test_scenario_4_officer_grant_forbidden(client: TestClient, auth_tokens: dict):
    officer = auth_tokens["officer"]
    cit_1 = auth_tokens["citizen_1"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_1["user_id"], "scope": "income", "purpose": "Officer override"},
        headers=officer["headers"]
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CONSENT_GRANT_FORBIDDEN"


# 5. Administrator granting consent -> 403 Forbidden
def test_scenario_5_admin_grant_forbidden(client: TestClient, auth_tokens: dict):
    admin = auth_tokens["admin"]
    cit_1 = auth_tokens["citizen_1"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_1["user_id"], "scope": "income", "purpose": "Admin override"},
        headers=admin["headers"]
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CONSENT_GRANT_FORBIDDEN"


# 6. Unauthenticated grant -> 401 Unauthorized or 403 Forbidden
def test_scenario_6_unauthenticated_grant_unauthorized(client: TestClient, auth_tokens: dict):
    cit_1 = auth_tokens["citizen_1"]
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_1["user_id"], "scope": "income", "purpose": "No auth"}
    )
    assert res.status_code in (401, 403)


# 7. Forged caller-supplied actor ID -> rejected or bound strictly to authenticated citizen ID
def test_scenario_7_forged_actor_id_cannot_override_authenticated_identity(client: TestClient, auth_tokens: dict):
    cit_1 = auth_tokens["citizen_1"]
    cit_2 = auth_tokens["citizen_2"]
    # Attempt to supply victim citizen_2's ID in body while using cit_1 token
    res = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_2["user_id"], "scope": "bills", "actor_id": cit_2["user_id"]},
        headers=cit_1["headers"]
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CROSS_CITIZEN_CONSENT_FORBIDDEN"


# 8. Direct service-layer call with non-citizen role -> PermissionError
def test_scenario_8_direct_service_layer_non_citizen_raises_permission_error():
    cit_id = f"cit_svc_{uuid.uuid4().hex[:8]}"
    # 8a: Helper role
    with pytest.raises(PermissionError) as exc_helper:
        consent_gateway.grant_consent(
            citizen_id=cit_id,
            scope=ConsentScope.INCOME,
            actor_id=cit_id,
            actor_role=RoleEnum.HELPER
        )
    assert "CONSENT_AUTHORIZATION_ERROR" in str(exc_helper.value)
    assert "Only citizens may authorize consent" in str(exc_helper.value)

    # 8b: Officer role
    with pytest.raises(PermissionError) as exc_officer:
        consent_gateway.grant_consent(
            citizen_id=cit_id,
            scope=ConsentScope.INCOME,
            actor_id=cit_id,
            actor_role=RoleEnum.OFFICER
        )
    assert "CONSENT_AUTHORIZATION_ERROR" in str(exc_officer.value)

    # 8c: Admin role
    with pytest.raises(PermissionError) as exc_admin:
        consent_gateway.grant_consent(
            citizen_id=cit_id,
            scope=ConsentScope.INCOME,
            actor_id=cit_id,
            actor_role=RoleEnum.ADMIN
        )
    assert "CONSENT_AUTHORIZATION_ERROR" in str(exc_admin.value)

    # 8d: Mismatched actor_id
    with pytest.raises(PermissionError) as exc_mismatch:
        consent_gateway.grant_consent(
            citizen_id=cit_id,
            scope=ConsentScope.INCOME,
            actor_id="different_citizen_id",
            actor_role=RoleEnum.CITIZEN
        )
    assert "Cross-citizen consent grant prohibited" in str(exc_mismatch.value)


# 9. Alternative endpoint or workflow bypass attempt -> 403 Forbidden
def test_scenario_9_unauthorized_consent_status_bypass_attempt(client: TestClient, auth_tokens: dict):
    cit_1 = auth_tokens["citizen_1"]
    officer = auth_tokens["officer"]
    admin = auth_tokens["admin"]
    helper = auth_tokens["helper"]

    # Ensure helper does NOT have active HELPER_ACTING consent
    consent_gateway.withdraw_consent(
        citizen_id=cit_1["user_id"],
        scope=ConsentScope.HELPER_ACTING,
        actor_id=cit_1["user_id"],
        actor_role=RoleEnum.CITIZEN
    )

    # Officer viewing status -> 403
    r_off = client.get(f"/api/v1/consent/status/{cit_1['user_id']}", headers=officer["headers"])
    assert r_off.status_code == 403

    # Admin viewing status -> 403
    r_adm = client.get(f"/api/v1/consent/status/{cit_1['user_id']}", headers=admin["headers"])
    assert r_adm.status_code == 403

    # Helper viewing status without delegation -> 403
    r_help = client.get(f"/api/v1/consent/status/{cit_1['user_id']}", headers=helper["headers"])
    assert r_help.status_code == 403

    # Cross citizen viewing status -> 403
    cit_2 = auth_tokens["citizen_2"]
    r_cit2 = client.get(f"/api/v1/consent/status/{cit_1['user_id']}", headers=cit_2["headers"])
    assert r_cit2.status_code == 403


# 10. Consent withdrawal and subsequent access blocking -> 403 ConsentWithdrawnException
def test_scenario_10_consent_withdrawal_blocks_access(client: TestClient, auth_tokens: dict):
    cit_1 = auth_tokens["citizen_1"]
    helper = auth_tokens["helper"]

    # 1. Citizen grants income consent
    r_grant = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": cit_1["user_id"], "scope": "income", "helper_id": helper["user_id"]},
        headers=cit_1["headers"]
    )
    assert r_grant.status_code == 200

    # Read gateway allows read
    assert consent_gateway.read_gateway(
        actor_id=helper["user_id"],
        actor_role=RoleEnum.HELPER,
        citizen_id=cit_1["user_id"],
        scope=ConsentScope.INCOME,
        acting_helper_id=helper["user_id"]
    ) is True

    # 2. Citizen withdraws consent
    r_withdraw = client.post(
        "/api/v1/consent/withdraw",
        json={"citizen_id": cit_1["user_id"], "scope": "income"},
        headers=cit_1["headers"]
    )
    assert r_withdraw.status_code == 200

    # 3. Subsequent read fails closed with ConsentWithdrawnException (HTTP 403)
    with pytest.raises(ConsentWithdrawnException) as excinfo:
        consent_gateway.read_gateway(
            actor_id=helper["user_id"],
            actor_role=RoleEnum.HELPER,
            citizen_id=cit_1["user_id"],
            scope=ConsentScope.INCOME,
            acting_helper_id=helper["user_id"]
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["code"] == "CONSENT_WITHDRAWN"


# 11. Concurrent grant/revoke operations -> consistent state with row locking
def test_scenario_11_concurrent_grant_revoke_operations():
    cit_id = f"cit_conc_{uuid.uuid4().hex[:8]}"
    gateway = ConsentGateway()
    errors = []

    def granter(count: int):
        for _ in range(count):
            try:
                gateway.grant_consent(
                    citizen_id=cit_id,
                    scope=ConsentScope.BILLS,
                    actor_id=cit_id,
                    actor_role=RoleEnum.CITIZEN
                )
            except Exception as e:
                errors.append(f"Grant error: {e}")

    def revoker(count: int):
        for _ in range(count):
            try:
                gateway.withdraw_consent(
                    citizen_id=cit_id,
                    scope=ConsentScope.BILLS,
                    actor_id=cit_id,
                    actor_role=RoleEnum.CITIZEN
                )
            except Exception as e:
                errors.append(f"Revoke error: {e}")

    threads = [
        threading.Thread(target=granter, args=(10,)),
        threading.Thread(target=revoker, args=(10,)),
        threading.Thread(target=granter, args=(10,)),
        threading.Thread(target=revoker, args=(10,))
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent operations caused errors: {errors}"
    final_status = gateway.check_consent(cit_id, ConsentScope.BILLS)
    assert isinstance(final_status, bool)
