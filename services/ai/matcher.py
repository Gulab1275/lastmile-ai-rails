"""
Identity Resolution & Fuzzy Matching Ladder (Challenge 03: Bad Data).
Matches citizens against mock NADRA identity records.
Enforces non-negotiable matching rules:
1. Exact CNIC + Name similarity >= 0.90: Auto-link.
2. Exact CNIC + Name similarity 0.70 - 0.90: Human review flag.
3. Different CNICs are NEVER merged under any circumstances.
"""
import re
from typing import Any, Dict, Tuple

from rapidfuzz import distance, fuzz

# Common Pakistani name prefixes, variants, and honorifics
NAME_VARIANTS = {
    "mohd": "muhammad",
    "mohammad": "muhammad",
    "mohammed": "muhammad",
    "muhammed": "muhammad",
    "md": "muhammad",
    "m.": "muhammad",
    "m": "muhammad",
    "ahmad": "ahmed",
    "syeda": "syed",
    "bibi": "",
    "begum": "",
    "khatoon": "",
    "mai": "",
    "fatimah": "fatima"
}

def clean_cnic(cnic: str) -> str:
    """Normalize CNIC by removing hyphens and whitespace."""
    if not cnic:
        return ""
    digits = re.sub(r"\D", "", cnic)
    if len(digits) == 13:
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
    return digits

def normalize_name(name: str) -> str:
    """Lowercase, strip honorifics, and standardize common variant spellings."""
    if not name:
        return ""
    tokens = re.sub(r"[^\w\s]", "", name.lower()).split()
    normalized = []
    for token in tokens:
        token_clean = NAME_VARIANTS.get(token, token)
        if token_clean:
            normalized.append(token_clean)
    return " ".join(normalized)

def compute_name_similarity(name1: str, name2: str) -> float:
    """Computes hybrid token-set ratio and Jaro-Winkler similarity."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    if not n1 or not n2:
        return 0.0

    # Token-set handles reversed name orders (e.g. "Ali Muhammad" vs "Muhammad Ali")
    token_set_sim = fuzz.token_sort_ratio(n1, n2) / 100.0
    jaro_sim = distance.JaroWinkler.similarity(n1, n2)

    # Weighted average giving high weight to token set
    return round(0.6 * token_set_sim + 0.4 * jaro_sim, 4)

def resolve_identity(input_claim: Dict[str, Any], registry_record: Dict[str, Any]) -> Tuple[float, str, Dict[str, Any]]:
    """
    Evaluates identity match confidence score (0.0 to 1.0).
    Returns (confidence_score, match_status, details)
    """
    input_cnic = clean_cnic(input_claim.get("cnic", ""))
    registry_cnic = clean_cnic(registry_record.get("cnic", ""))

    input_name = input_claim.get("full_name", "")
    registry_name = registry_record.get("full_name", "")

    # Non-negotiable Rule: Empty inputs cannot match
    if not input_cnic or not registry_cnic:
        return 0.0, "missing_cnic", {
            "reason": "CNIC is missing or invalid format",
            "requires_proof": True
        }

    # Non-negotiable Rule: Different CNICs NEVER merge
    if input_cnic != registry_cnic:
        return 0.0, "cnic_mismatch", {
            "reason": "CNIC does not match registry record. Two different CNICs are never merged.",
            "input_cnic": input_cnic,
            "registry_cnic": registry_cnic,
            "requires_proof": True
        }

    # CNIC matches exactly. Now evaluate name similarity ladder:
    name_sim = compute_name_similarity(input_name, registry_name)

    details = {
        "cnic_match": True,
        "input_name_normalized": normalize_name(input_name),
        "registry_name_normalized": normalize_name(registry_name),
        "name_similarity": name_sim
    }

    if name_sim >= 0.90:
        # High confidence match (clean or minor variant)
        return 1.0, "verified_match", details
    elif name_sim >= 0.70:
        # Probable variant or spelling typo -> escalate to human review with notes
        return round(name_sim, 2), "probable_variant_review", details
    else:
        # Serious name mismatch on same CNIC -> flag potential identity conflict
        return 0.25, "identity_conflict", details
