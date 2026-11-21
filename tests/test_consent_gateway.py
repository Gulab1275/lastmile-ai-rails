"""
Tests for Consent Gateway and Immediate Revocation Enforcement.
Implements Hackathon Challenge 06: Consent and Take-Back.
"""
import pytest

from services.api.engine.consent_gateway import ConsentGateway, ConsentWithdrawnException
from services.shared.schemas import ConsentScope, RoleEnum


def test_consent_grant_and_check():
    gateway = ConsentGateway()
    citizen_id = "cit_123"

    # Reset any existing persistent state from prior test runs
    if gateway.check_consent(citizen_id, ConsentScope.IDENTITY):
        gateway.withdraw_consent(citizen_id, ConsentScope.IDENTITY)

    assert gateway.check_consent(citizen_id, ConsentScope.IDENTITY) is False

    record = gateway.grant_consent(citizen_id, ConsentScope.IDENTITY)
    assert record.granted is True
    assert gateway.check_consent(citizen_id, ConsentScope.IDENTITY) is True


def test_consent_withdrawal_blocks_access_immediately():
    """
    Verifies that withdrawing consent immediately causes read_gateway()
    to raise HTTP 403 ConsentWithdrawnException.
    """
    gateway = ConsentGateway()
    citizen_id = "cit_parveen"

    # 1. Grant consent
    gateway.grant_consent(citizen_id, ConsentScope.INCOME)
    assert gateway.read_gateway("usr_actor", RoleEnum.OFFICER, citizen_id, ConsentScope.INCOME) is True

    # 2. Citizen withdraws consent
    gateway.withdraw_consent(citizen_id, ConsentScope.INCOME)

    # 3. Subsequent read attempt MUST be blocked with HTTP 403
    with pytest.raises(ConsentWithdrawnException) as exc_info:
        gateway.read_gateway("usr_actor", RoleEnum.OFFICER, citizen_id, ConsentScope.INCOME)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "CONSENT_WITHDRAWN"


def test_helper_acting_consent_verification():
    """
    A helper can only act if granted_to_helper_id matches the acting helper.
    """
    gateway = ConsentGateway()
    citizen_id = "cit_family_4"
    authorized_helper = "hlp_shazia"
    imposter_helper = "hlp_imposter"

    gateway.grant_consent(
        citizen_id=citizen_id,
        scope=ConsentScope.HELPER_ACTING,
        helper_id=authorized_helper
    )

    # Authorized helper check passes
    assert gateway.check_consent(citizen_id, ConsentScope.HELPER_ACTING, authorized_helper) is True

    # Imposter helper check fails
    assert gateway.check_consent(citizen_id, ConsentScope.HELPER_ACTING, imposter_helper) is False
