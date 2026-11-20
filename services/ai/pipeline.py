"""
Claim Pipeline & Deterministic Decision Engine (Challenge 01 & 02).
Implements the 6-step evaluation graph:
intake -> extract_docs -> resolve_identity -> check_scam -> evaluate_rules -> score_risk -> router.
Rules:
1. The LLM never makes the approval decision. Deterministic cost-optimized rules decide.
2. Confidence is the weakest link: overall = min(components).
3. The system never auto-rejects. Rejections require human officer confirmation.
"""
import uuid
from typing import Dict, Any, List, Optional
from services.shared.schemas import (
    RouteDecision, ComponentScores, ReasonSimple, DecisionResponse
)
from services.ai.matcher import resolve_identity
from services.ai.scam import classify_message
from db.connection import SessionLocal
from db.models import Case, Citizen, Document, RuleVersion, Decision, ReviewItem, AuditLog

MAX_AUTO_APPROVE_AMOUNT = 25000.0

def evaluate_claim_pipeline(case_id: str) -> DecisionResponse:
    session = SessionLocal()
    steps_taken = []
    try:
        case = session.query(Case).filter_by(id=case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")

        citizen = case.citizen
        form_data = case.form_data or {}
        claim_amount = case.claim_amount or 0.0

        # Step 1: Document & OCR evaluation
        docs = session.query(Document).filter_by(case_id=case_id).all()
        missing_docs = []
        doc_types = {d.doc_type for d in docs}
        
        if "cnic_front" not in doc_types:
            missing_docs.append("cnic_front")
        if "utility_bill" not in doc_types:
            missing_docs.append("utility_bill")

        ocr_score = 0.95 if docs and not any(d.blur_score < 90 for d in docs) else (0.50 if docs else 0.0)
        auth_score = max(0.0, 1.0 - max([d.tamper_score for d in docs], default=0.0))

        # Step 2: Identity Resolution with mock NADRA ladder
        mock_registry = {
            "cnic": citizen.cnic,
            "full_name": citizen.full_name
        }
        id_score, id_status, id_details = resolve_identity(form_data, mock_registry)

        # Step 3: Scam & Risk Safety check
        scam_safety = 1.0
        if "message_text" in form_data:
            scam_res = classify_message(form_data["message_text"])
            scam_safety = round(1.0 - scam_res["scam_probability"], 3)

        # Step 4: Rules Engine (Check active rule version)
        active_rule = session.query(RuleVersion).filter_by(status="active").order_by(RuleVersion.version.desc()).first()
        rule_version_num = active_rule.version if active_rule else 1
        
        rules_passed = True
        missing_fields = []
        monthly_income = form_data.get("monthly_income", citizen.monthly_income)
        household_size = form_data.get("household_size", citizen.household_size)

        if monthly_income is None:
            missing_fields.append("monthly_income")
            rules_passed = False
        elif monthly_income > 45000:
            rules_passed = False

        if household_size is None or household_size < 1:
            missing_fields.append("household_size")
            rules_passed = False

        rules_complete_score = 1.0 if (rules_passed and not missing_fields) else (0.40 if missing_fields else 0.20)

        # Step 5: Decision Maker - Weakest Link Confidence
        components = ComponentScores(
            identity=round(id_score, 3),
            ocr=round(ocr_score, 3),
            authenticity=round(auth_score, 3),
            rules_complete=round(rules_complete_score, 3),
            scam_safety=round(scam_safety, 3)
        )

        overall_confidence = min(
            components.identity,
            components.ocr,
            components.authenticity,
            components.rules_complete,
            components.scam_safety
        )
        p_wrong = round(1.0 - overall_confidence, 3)

        # Step 6: Cost-Optimized Routing
        # Cost model: wrong approval=10, wrong block=3, human review=1, ask proof=0.4
        all_missing = missing_docs + missing_fields

        if p_wrong <= 0.05 and claim_amount <= MAX_AUTO_APPROVE_AMOUNT and not all_missing:
            route = RouteDecision.AUTO_APPROVE
            approval_token = f"tok_auto_{uuid.uuid4().hex[:12]}"
            reason_en = f"Claim automatically approved under threshold PKR {claim_amount:,.0f} with all identity and document checks verified."
            reason_ur = f"تمام شناختی اور دستاویزی جانچ مکمل ہونے پر آپ کی امدادی رقم {claim_amount:,.0f} روپے منظور کر لی گئی ہے۔"
        elif (0.05 < p_wrong <= 0.30 or all_missing) and len(all_missing) > 0:
            route = RouteDecision.ASK_MORE_PROOF
            approval_token = None
            missing_str = ", ".join(all_missing)
            reason_en = f"Please provide clearer documents or missing fields: {missing_str}."
            reason_ur = f"براہ کرم ضروری دستاویزات یا معلومات فراہم کریں: {missing_str}"
        else:
            route = RouteDecision.HUMAN_REVIEW
            approval_token = None
            reason_en = "Claim routed to a welfare review officer for manual verification due to conflicting or uncertain records."
            reason_ur = "معلومات کی مزید تصدیق کے لیے کیس کو متعلقہ فلاحی افسر کے پاس بھیج دیا گیا ہے۔"

        decision_resp = DecisionResponse(
            case_id=case_id,
            route=route,
            confidence=overall_confidence,
            components=components,
            missing=all_missing,
            reason_simple=ReasonSimple(en=reason_en, ur=reason_ur),
            rule_version=rule_version_num
        )

        # Persist Decision in Supabase
        existing_dec = session.query(Decision).filter_by(case_id=case_id).first()
        if existing_dec:
            existing_dec.route = route.value
            existing_dec.confidence = overall_confidence
            existing_dec.component_scores = components.model_dump()
            existing_dec.rule_version_id = active_rule.id if active_rule else 1
            existing_dec.reason_simple = decision_resp.reason_simple.model_dump()
            existing_dec.auditor_trace = {
                "p_wrong": p_wrong,
                "missing": all_missing,
                "id_details": id_details
            }
            existing_dec.approval_token = approval_token
        else:
            new_dec = Decision(
                case_id=case_id,
                route=route.value,
                confidence=overall_confidence,
                component_scores=components.model_dump(),
                rule_version_id=active_rule.id if active_rule else 1,
                reason_simple=decision_resp.reason_simple.model_dump(),
                auditor_trace={
                    "p_wrong": p_wrong,
                    "missing": all_missing,
                    "id_details": id_details
                },
                approval_token=approval_token
            )
            session.add(new_dec)

        # If human review, ensure review queue item exists
        if route == RouteDecision.HUMAN_REVIEW:
            rev_item = session.query(ReviewItem).filter_by(case_id=case_id).first()
            if not rev_item:
                new_rev = ReviewItem(
                    case_id=case_id,
                    priority=1 if claim_amount > 20000 else 2,
                    confidence=overall_confidence,
                    handoff_packet={
                        "p_wrong": p_wrong,
                        "components": components.model_dump(),
                        "missing": all_missing,
                        "citizen_name": citizen.full_name,
                        "cnic": citizen.cnic
                    },
                    status="pending"
                )
                session.add(new_rev)

        # Log action in append-only cryptographic audit log
        AuditLog.create_entry(
            session=session,
            actor="decision_engine",
            action="evaluate_claim",
            target=f"case:{case_id}",
            result=route.value,
            request_id=str(uuid.uuid4())
        )

        session.commit()
        return decision_resp

    finally:
        session.close()

def run_claim_agent(case_id: str) -> Dict[str, Any]:
    """Public function exposed to API."""
    decision = evaluate_claim_pipeline(case_id)
    return {
        "case_id": case_id,
        "decision": decision.model_dump(),
        "status": "evaluated"
    }
