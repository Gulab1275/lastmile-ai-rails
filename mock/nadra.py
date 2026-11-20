"""
Mock NADRA Identity Service.
Simulates Pakistan's National Database and Registration Authority.
Supports:
- Exact CNIC lookup
- Fuzzy name matching (handles variant spellings: Muhammad/Mohammad, etc.)
- Chaos modes (timeout, 500, slow, bad_data)
"""
from difflib import SequenceMatcher
from typing import Any, Dict, Optional

from mock.chaos import apply_chaos
from services.shared.schemas import MockNADRARequest, MockNADRAResponse

# Realistic Mock Citizen Registry (Simulated, no real personal data)
MOCK_CITIZEN_REGISTRY: Dict[str, Dict[str, Any]] = {
    "42101-1234567-1": {
        "full_name": "Parveen Bibi",
        "name_variants": ["Parveen Bibi", "Parveen Akhtar", "پروین بی بی"],
        "father_husband_name": "Muhammad Rafiq",
        "deceased": False,
        "family_head_cnic": "42101-1234567-1",
        "status": "VERIFIED"
    },
    "42101-7654321-2": {
        "full_name": "Mohammad Tariq",
        "name_variants": ["Mohammad Tariq", "Muhammad Tariq", "Mohd Tariq", "محمد طارق"],
        "father_husband_name": "Abdul Karim",
        "deceased": False,
        "family_head_cnic": "42101-7654321-2",
        "status": "VERIFIED"
    },
    "42201-9876543-3": {
        "full_name": "Fatima Zahra",
        "name_variants": ["Fatima Zahra", "Fatima Zehra", "فاطمہ زہرا"],
        "father_husband_name": "Ghulam Abbas",
        "deceased": False,
        "family_head_cnic": "42201-9876543-3",
        "status": "VERIFIED"
    },
    "42301-5555555-5": {
        "full_name": "Deceased Record Test",
        "name_variants": ["Deceased Record Test"],
        "father_husband_name": "Unknown",
        "deceased": True,
        "family_head_cnic": None,
        "status": "DECEASED"
    }
}


def normalize_cnic(cnic: str) -> str:
    """Normalize CNIC to standard hyphenated format: XXXXX-XXXXXXX-X."""
    digits = "".join(filter(str.isdigit, cnic))
    if len(digits) == 13:
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
    return cnic


def name_similarity(name1: str, name2: str) -> float:
    """Calculates string similarity ratio ignoring case and whitespace."""
    s1 = " ".join(name1.lower().split())
    s2 = " ".join(name2.lower().split())
    return SequenceMatcher(None, s1, s2).ratio()


async def verify_identity_nadra(
    req: MockNADRARequest,
    chaos_mode: Optional[str] = None
) -> MockNADRAResponse:
    """
    Simulates NADRA Citizen Identity Verification.
    """
    await apply_chaos(chaos_mode)

    norm_cnic = normalize_cnic(req.cnic)
    citizen_record = MOCK_CITIZEN_REGISTRY.get(norm_cnic)

    if not citizen_record:
        # Check if citizen exists without hyphens
        for stored_cnic, rec in MOCK_CITIZEN_REGISTRY.items():
            if "".join(filter(str.isdigit, stored_cnic)) == "".join(filter(str.isdigit, req.cnic)):
                citizen_record = rec
                norm_cnic = stored_cnic
                break

    if not citizen_record:
        # If CNIC is not in the mock database, simulate a realistic non-match or synthetic low-score match
        sim_score = max(name_similarity(req.full_name, "Muhammad Ali"), 0.35)
        return MockNADRAResponse(
            matched=False,
            match_score=round(sim_score, 2),
            canonical_cnic=norm_cnic,
            canonical_name="NOT_FOUND",
            deceased=False,
            status="RECORD_NOT_FOUND",
            latency_ms=150
        )

    # Compute best fuzzy match among name variants
    best_score = max(name_similarity(req.full_name, v) for v in citizen_record["name_variants"])

    is_matched = best_score >= 0.70 and not citizen_record["deceased"]

    return MockNADRAResponse(
        matched=is_matched,
        match_score=round(best_score, 2),
        canonical_cnic=norm_cnic,
        canonical_name=citizen_record["full_name"],
        family_head_cnic=citizen_record.get("family_head_cnic"),
        deceased=citizen_record["deceased"],
        status=citizen_record["status"] if not citizen_record["deceased"] else "DECEASED",
        latency_ms=120
    )
