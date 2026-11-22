"""
Decision Engine with Weakest-Link Confidence and Cost Matrix Threshold Routing.
Implements Hackathon Principles:
1. The LLM never makes the approval decision.
2. Confidence is the weakest link: min(components).
3. The system never auto-rejects.
4. Gated Cryptographic Tokens for disbursements.
"""
import hashlib
import hmac
import os
from typing import Any, Dict, List, Optional

from services.api.config import settings
from services.api.engine.rules_engine import rules_engine
from services.shared.schemas import (
    ComponentScores,
    DecisionResponse,
    HandoffPacket,
    ReasonSimple,
    RouteDecision,
)


def _get_approval_secret() -> str:
    """Returns the securely configured secret key for approval tokens. Fails closed if missing."""
    custom = os.getenv("APPROVAL_TOKEN_SECRET") or getattr(settings, "APPROVAL_TOKEN_SECRET", None)
    if not custom or not str(custom).strip():
        raise RuntimeError(
            "CRITICAL_SECURITY_ERROR: APPROVAL_TOKEN_SECRET is not configured. "
            "Silent fallback to SECRET_KEY is strictly prohibited. Approval tokens cannot be issued."
        )
    key_str = str(custom).strip()
    if len(key_str) < 32:
        raise RuntimeError(
            f"CRITICAL_SECURITY_ERROR: APPROVAL_TOKEN_SECRET must be at least 32 characters (got {len(key_str)})."
        )
    if key_str == settings.SECRET_KEY:
        raise RuntimeError(
            "CRITICAL_SECURITY_ERROR: Cryptographic key separation violation. "
            "APPROVAL_TOKEN_SECRET must be distinct from SECRET_KEY."
        )
    return key_str


def generate_approval_token(case_id: str, rule_version: int, confidence: float) -> str:
    """Generates a verifiable HMAC-SHA256 approval token for gated disbursement."""
    secret = _get_approval_secret()
    data = f"{case_id}:{rule_version}:{confidence:.4f}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


def verify_approval_token(token: str, case_id: str, rule_version: int, confidence: float) -> bool:
    """Verifies HMAC-SHA256 approval token."""
    expected = generate_approval_token(case_id, rule_version, confidence)
    return hmac.compare_digest(token, expected)


class DecisionEngine:
    def __init__(self):
        pass

    def evaluate_case(
        self,
        case_id: str,
        case_data: Dict[str, Any],
        component_scores: ComponentScores,
        missing_docs: Optional[List[str]] = None,
        tamper_flags: Optional[List[str]] = None
    ) -> DecisionResponse:
        """
        Evaluates a case deterministically.
        - Calculates Weakest-Link Confidence: min(identity, ocr, authenticity, rules_complete, scam_safety).
        - Probability of wrong decision: p_wrong = 1.0 - overall_confidence.
        - Evaluates cost matrix thresholds from active rule set.
        """
        active_rules = rules_engine.get_active_rules()
        missing = missing_docs or []
        flags = tamper_flags or []

        # 1. Weakest Link Confidence
        component_values = [
            component_scores.identity,
            component_scores.ocr,
            component_scores.authenticity,
            component_scores.rules_complete,
            component_scores.scam_safety
        ]
        overall_confidence = min(component_values)
        p_wrong = 1.0 - overall_confidence

        # 2. Evaluate Rule Set
        rule_trace = rules_engine.evaluate(case_data, version=active_rules.version)
        requested_amount = float(case_data.get("requested_amount", 12000.0))

        # 3. Decision Routing Logic
        # Route 1: Auto-Approve
        # Condition: p_wrong <= max_wrong_prob (0.05), rules passed, under cap, no missing docs, no tamper flags
        can_auto_approve = (
            p_wrong <= active_rules.max_wrong_prob_auto_approve
            and rule_trace.passed_all
            and requested_amount <= active_rules.max_auto_approve_amount
            and len(missing) == 0
            and len(flags) == 0
        )

        if can_auto_approve:
            route = RouteDecision.AUTO_APPROVE
            token = generate_approval_token(case_id, active_rules.version, overall_confidence)
            reason = ReasonSimple(
                en="All identity checks, document verifications, and eligibility rules passed with high confidence. Approved automatically.",
                ur="شناخت کی تصدیق، دستاویزات اور اہلیت کے تمام قواعد کامیابی سے مکمل ہو گئے۔ خودکار منظوری دی گئی ہے۔"
            )
        # Route 2: Ask for More Proof
        # Condition: Moderate risk (0.05 < p_wrong <= 0.30) OR specific missing/blurry document, but rules fundamentally feasible
        elif (p_wrong <= active_rules.max_wrong_prob_ask_proof or len(missing) > 0) and not flags:
            route = RouteDecision.ASK_MORE_PROOF
            token = None
            if len(missing) > 0:
                missing_str_en = ", ".join(missing)
                reason = ReasonSimple(
                    en=f"Additional clear proof required: {missing_str_en}. Please take a clearer photo.",
                    ur=f"مزید واضح دستاویز کی ضرورت ہے: {missing_str_en}۔ برائے مہربانی صاف تصویر اپ لوڈ کریں۔"
                )
            else:
                reason = ReasonSimple(
                    en="Document text was partially unclear or confidence was borderline. Please upload a clearer copy.",
                    ur="دستاویز کے کچھ حصے واضح نہیں تھے۔ برائے مہربانی مزید واضح تصویر فراہم کریں۔"
                )
        # Route 3: Human Officer Review (Never auto-reject!)
        # Condition: p_wrong > 0.30, failed eligibility rules, suspected tampering, or high financial claim
        else:
            route = RouteDecision.HUMAN_REVIEW
            token = None
            if not rule_trace.passed_all:
                failed_en = "; ".join(rule_trace.failed_conditions)
                reason = ReasonSimple(
                    en=f"Case routed to a Department Officer for human review due to eligibility criteria: {failed_en}.",
                    ur="کیس محکمانہ افسر کے پاس جائزے کے لیے بھیج دیا گیا ہے کیونکہ قواعد کی تصدیق درکار ہے۔"
                )
            elif flags:
                reason = ReasonSimple(
                    en="Case routed to a Department Officer for manual document verification.",
                    ur="دستاویزات کی تصدیق کے لیے کیس محکمانہ افسر کو بھیج دیا گیا ہے۔"
                )
            else:
                reason = ReasonSimple(
                    en="Case confidence requires officer verification. A human officer will review your claim shortly.",
                    ur="کیس کا جائزہ محکمانہ افسر لے گا۔ جلد آپ کو فیصلے سے آگاہ کیا جائے گا۔"
                )

        return DecisionResponse(
            case_id=case_id,
            route=route,
            confidence=round(overall_confidence, 4),
            components=component_scores,
            missing=missing,
            reason_simple=reason,
            rule_version=active_rules.version,
            approval_token=token
        )

    def build_handoff_packet(
        self,
        case_id: str,
        case_data: Dict[str, Any],
        decision: DecisionResponse,
        flags: Optional[List[str]] = None
    ) -> HandoffPacket:
        """
        Builds a comprehensive handoff packet for the Department Officer review queue.
        Implements Challenge 02: Saying 'I Am Not Sure' with attached case notes.
        """
        rule_trace = rules_engine.evaluate(case_data, version=decision.rule_version)
        detected_flags = flags or []

        if not rule_trace.passed_all:
            detected_flags.extend(rule_trace.failed_conditions)
        if decision.components.identity < 0.70:
            detected_flags.append(f"Low identity confidence ({decision.components.identity:.2f})")
        if decision.components.ocr < 0.75:
            detected_flags.append(f"Low OCR quality ({decision.components.ocr:.2f})")
        if decision.components.authenticity < 0.80:
            detected_flags.append(f"Potential document alteration flag ({decision.components.authenticity:.2f})")

        # Priority score (0.0 to 10.0): Lower confidence + higher claim amount = higher priority
        claim_amt = float(case_data.get("requested_amount", 12000.0))
        amt_factor = min(claim_amt / 25000.0, 1.0) * 4.0
        risk_factor = (1.0 - decision.confidence) * 6.0
        priority_score = round(min(amt_factor + risk_factor, 10.0), 2)

        suggested_action = (
            "Verify citizen identity manually against physical record."
            if decision.components.identity < 0.70
            else "Inspect utility bill proof and confirm household income."
        )

        return HandoffPacket(
            case_id=case_id,
            priority_score=priority_score,
            overall_confidence=decision.confidence,
            component_breakdown=decision.components,
            flags=detected_flags,
            rule_trace=rule_trace,
            suggested_action=suggested_action,
            citizen_summary={
                "name": case_data.get("citizen_name"),
                "cnic": case_data.get("cnic"),
                "phone": case_data.get("phone"),
                "household_size": case_data.get("household_size"),
                "monthly_income": case_data.get("monthly_income"),
                "requested_amount": case_data.get("requested_amount"),
            }
        )


# Global Singleton Decision Engine
decision_engine = DecisionEngine()
