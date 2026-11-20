"""
Dual-View Explanation Builder.
Implements Challenge 05: Explain and Audit.
Produces:
1. Citizen View: Simple, low-literacy friendly Urdu & English with icon cues.
2. Auditor View: Full technical trace, rule version, component confidences, and audit hash reference.
"""
from typing import Any, Dict

from services.shared.schemas import DecisionResponse, RouteDecision


class ExplanationBuilder:
    @staticmethod
    def build_citizen_view(decision: DecisionResponse) -> Dict[str, Any]:
        """
        Formats a simple, visual, voice-ready explanation for low-literacy citizens.
        Uses clear icons and bilingual text.
        """
        icon_map = {
            RouteDecision.AUTO_APPROVE: "✅",
            RouteDecision.ASK_MORE_PROOF: "📄",
            RouteDecision.HUMAN_REVIEW: "⏳"
        }

        headline_en = {
            RouteDecision.AUTO_APPROVE: "Your relief grant is approved!",
            RouteDecision.ASK_MORE_PROOF: "Please send a clearer photo of your document.",
            RouteDecision.HUMAN_REVIEW: "Your case is with the government officer for review."
        }

        headline_ur = {
            RouteDecision.AUTO_APPROVE: "آپ کی مالی امداد منظور ہو گئی ہے!",
            RouteDecision.ASK_MORE_PROOF: "برائے مہربانی اپنی دستاویز کی صاف تصویر فراہم کریں۔",
            RouteDecision.HUMAN_REVIEW: "آپ کا کیس جائزے کے لیے سرکاری افسر کے پاس ہے۔"
        }

        return {
            "status_icon": icon_map.get(decision.route, "ℹ️"),
            "headline_en": headline_en.get(decision.route, "Case updated"),
            "headline_ur": headline_ur.get(decision.route, "کیس اپ ڈیٹ ہو گیا"),
            "reason_en": decision.reason_simple.en,
            "reason_ur": decision.reason_simple.ur,
            "missing_items": decision.missing,
            "voice_audio_cue": "tts_ready"
        }

    @staticmethod
    def build_auditor_view(
        decision: DecisionResponse,
        case_data: Dict[str, Any],
        audit_hash: str
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive technical audit trace for inspectors and compliance auditors.
        """
        return {
            "case_id": decision.case_id,
            "decision_route": decision.route.value,
            "overall_confidence": decision.confidence,
            "weakest_link_rule_applied": "min(identity, ocr, authenticity, rules_complete, scam_safety)",
            "component_confidences": {
                "identity_match": decision.components.identity,
                "ocr_clarity": decision.components.ocr,
                "document_authenticity": decision.components.authenticity,
                "rules_eligibility": decision.components.rules_complete,
                "scam_safety_score": decision.components.scam_safety
            },
            "rule_version_applied": decision.rule_version,
            "evaluated_at": decision.evaluated_at.isoformat(),
            "gated_approval_token_generated": bool(decision.approval_token),
            "cryptographic_audit_hash": audit_hash,
            "case_inputs_evaluated": {
                "citizen_name": case_data.get("citizen_name"),
                "cnic": case_data.get("cnic"),
                "household_size": case_data.get("household_size"),
                "monthly_income": case_data.get("monthly_income"),
                "requested_amount": case_data.get("requested_amount"),
            }
        }
