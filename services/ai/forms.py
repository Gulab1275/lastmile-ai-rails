"""
Structured Form Extraction Pipeline (Task N8 / Challenge 07: Works for Everyone).
Extracts validated claim fields (CNIC, name, household size, income, phone)
from unstructured conversational Urdu / English speech transcripts.
"""
import json
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from services.ai.router import route_llm


class ExtractedClaimForm(BaseModel):
    full_name: Optional[str] = Field(None, description="Citizen full name")
    cnic: Optional[str] = Field(None, description="13-digit CNIC in 42101-1234567-1 format")
    phone: Optional[str] = Field(None, description="Pakistani mobile number")
    household_size: Optional[int] = Field(None, ge=1, description="Total family members in household")
    monthly_income: Optional[float] = Field(None, ge=0.0, description="Monthly household income in PKR")
    benefit_requested: str = Field(default="relief_cash_grant")
    missing_fields: List[str] = Field(default_factory=list, description="Fields required by rules but not yet provided")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

def extract_regex_heuristics(text: str) -> Dict[str, Any]:
    """Fast deterministic regex extraction for CNIC, Phone, and numbers."""
    extracted = {}

    # CNIC matching: 42101-1234567-1 or 4210112345671
    cnic_match = re.search(r"\b\d{5}[-\s]?\d{7}[-\s]?\d{1}\b", text)
    if cnic_match:
        digits = re.sub(r"\D", "", cnic_match.group(0))
        if len(digits) == 13:
            extracted["cnic"] = f"{digits[:5]}-{digits[5:12]}-{digits[12]}"

    # Pakistani Mobile number matching: 03XX-XXXXXXX or 03XXXXXXXXX
    phone_match = re.search(r"\b(03\d{2})[-\s]?(\d{7})\b", text)
    if phone_match:
        extracted["phone"] = f"{phone_match.group(1)}{phone_match.group(2)}"

    # Household size heuristic (e.g., "5 افراد", "4 family members", "6 بچے")
    hh_match = re.search(r"\b(\d{1,2})\s*(?:افراد|لوگ|family members|bache|members|persons)\b", text, re.IGNORECASE)
    if hh_match:
        extracted["household_size"] = int(hh_match.group(1))

    # Income heuristic (e.g., "25000 آمدنی", "income 30000", "20 ہزار روپے")
    inc_match = re.search(r"\b(\d{4,6})\s*(?:آمدنی|روپے|income|salary|pkr)\b", text, re.IGNORECASE)
    if inc_match:
        extracted["monthly_income"] = float(inc_match.group(1))
    elif re.search(r"(\d{1,2})\s*ہزار", text):
        k_match = re.search(r"(\d{1,2})\s*ہزار", text)
        extracted["monthly_income"] = float(k_match.group(1)) * 1000.0

    return extracted

def extract_claim_form(conversational_text: str) -> ExtractedClaimForm:
    """
    Combines deterministic regex extraction with LLM reasoning
    to convert messy spoken Urdu/English intake into a validated Pydantic form.
    """
    if not conversational_text or not conversational_text.strip():
        return ExtractedClaimForm(
            missing_fields=["cnic", "full_name", "household_size", "monthly_income"]
        )

    # 1. First pass: Fast deterministic regex
    pre_extracted = extract_regex_heuristics(conversational_text)

    # 2. Second pass: LLM Structured Output extraction
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert public relief data intake system. "
                "Analyze the user's conversational statement (which may be in conversational Urdu, Roman Urdu, or English). "
                "Extract the following fields into a clean JSON object:\n"
                "- full_name (string or null)\n"
                "- cnic (string in 'XXXXX-XXXXXXX-X' format or null)\n"
                "- phone (string or null)\n"
                "- household_size (integer or null)\n"
                "- monthly_income (float in PKR or null)\n\n"
                "Respond ONLY with a valid JSON object matching these keys. Do not include markdown code fences or conversational prose."
            )
        },
        {
            "role": "user",
            "content": f"Statement:\n\"{conversational_text}\""
        }
    ]

    llm_res = route_llm(prompt_messages, temperature=0.0)
    raw_content = llm_res.get("content", "").strip()

    # Clean JSON
    if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
    if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
    raw_content = raw_content.strip()

    parsed = {}
    try:
        parsed = json.loads(raw_content)
    except Exception:
        parsed = {}

    # Merge heuristic results (heuristics take precedence for exact CNIC and phone formats)
    final_cnic = pre_extracted.get("cnic") or parsed.get("cnic")
    final_name = parsed.get("full_name") or pre_extracted.get("full_name")
    final_phone = pre_extracted.get("phone") or parsed.get("phone")
    final_hh = pre_extracted.get("household_size") or parsed.get("household_size")
    final_income = pre_extracted.get("monthly_income") or parsed.get("monthly_income")

    # Detect missing required fields for the rulebook
    missing = []
    if not final_cnic:
        missing.append("cnic")
    if not final_name:
        missing.append("full_name")
    if not final_hh:
        missing.append("household_size")
    if final_income is None:
        missing.append("monthly_income")

    confidence = round(max(0.2, 1.0 - (len(missing) * 0.2)), 2)

    return ExtractedClaimForm(
        full_name=final_name,
        cnic=final_cnic,
        phone=final_phone,
        household_size=int(final_hh) if final_hh else None,
        monthly_income=float(final_income) if final_income is not None else None,
        missing_fields=missing,
        confidence=confidence
    )
