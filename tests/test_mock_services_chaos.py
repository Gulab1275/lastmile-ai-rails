"""
Tests for Mock External DPI Rails and Chaos Engineering Modes.
Simulates Pakistan's public rails:
1. NADRA Identity Verification with fuzzy name matching
2. Raast Instant Payment with gated cryptographic authorization token
3. Complaints Portal
4. Chaos modes (timeout, 500, slow)
"""
import asyncio

import pytest
from fastapi import HTTPException

from mock.nadra import verify_identity_nadra
from mock.raast import disburse_raast
from services.shared.schemas import MockNADRARequest, MockRaastRequest


def test_mock_nadra_exact_and_fuzzy_match():
    async def _run():
        # Exact match
        req_exact = MockNADRARequest(cnic="42101-1234567-1", full_name="Parveen Bibi")
        resp_exact = await verify_identity_nadra(req_exact)
        assert resp_exact.matched is True
        assert resp_exact.match_score == 1.0

        # Fuzzy match with spelling variant (Mohd Tariq vs Mohammad Tariq)
        req_fuzzy = MockNADRARequest(cnic="42101-7654321-2", full_name="Mohd Tariq")
        resp_fuzzy = await verify_identity_nadra(req_fuzzy)
        assert resp_fuzzy.matched is True
        assert resp_fuzzy.match_score >= 0.70

    asyncio.run(_run())


def test_mock_raast_gated_token_enforcement():
    """
    HIGH RISK PAYMENT PROTECTION:
    Disbursement without a valid cryptographic approval token is rejected with HTTP 403.
    """
    async def _run():
        req_invalid_token = MockRaastRequest(
            idempotency_key="idemp_test_001",
            case_id="cas_test_99",
            receiver_iban_or_raast_id="PK99RAAST1234567890",
            amount=12000.0,
            approval_token=""  # Missing token!
        )
        with pytest.raises(HTTPException) as exc_info:
            await disburse_raast(req_invalid_token)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "GATED_DISBURSEMENT_UNAUTHORIZED"

    asyncio.run(_run())


def test_mock_raast_idempotency():
    """
    Duplicate payment requests with the same idempotency key
    must return the exact same transaction without duplicate deductions.
    """
    async def _run():
        req = MockRaastRequest(
            idempotency_key="idemp_unique_key_123",
            case_id="cas_test_idemp",
            receiver_iban_or_raast_id="PK99RAAST1234567890",
            amount=10000.0,
            approval_token="valid_cryptographic_token_at_least_16_chars"
        )
        resp1 = await disburse_raast(req)
        resp2 = await disburse_raast(req)

        assert resp1.transaction_id == resp2.transaction_id
        assert resp1.settled_at == resp2.settled_at

    asyncio.run(_run())


def test_chaos_mode_500_failure():
    """Verifies simulated DPI rail 500 error when chaos=500."""
    async def _run():
        req = MockNADRARequest(cnic="42101-1234567-1", full_name="Parveen Bibi")
        with pytest.raises(HTTPException) as exc_info:
            await verify_identity_nadra(req, chaos_mode="500")
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["code"] == "PUBLIC_RAIL_UNAVAILABLE"

    asyncio.run(_run())
