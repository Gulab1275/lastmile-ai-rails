"""
Decision Engine & Dual-View Explanation Endpoints.
Evaluates claims deterministically, computes weakest-link confidence, and provides explainability.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from services.api.engine.audit_log import audit_log
from services.api.engine.consent_gateway import consent_gateway
from services.api.engine.decision_engine import decision_engine
from services.api.engine.explanation_builder import ExplanationBuilder
from services.api.routes.cases import _CASES_DB
from services.api.security.rbac import get_current_user
from services.shared.schemas import (
    CaseStatus,
    ComponentScores,
    ConsentScope,
    DecisionResponse,
    RoleEnum,
    RouteDecision,
    UserResponse,
)

router = APIRouter(prefix="/decisions", tags=["Decision Engine & Explainability"])


@router.post("/evaluate/{case_id}", response_model=DecisionResponse)
async def evaluate_case_decision(
    case_id: str,
    component_scores: Optional[ComponentScores] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Evaluates a case deterministically through the Decision Engine.
    - Computes weakest-link confidence = min(identity, ocr, authenticity, rules_complete, scam_safety).
    - Checks cost matrix thresholds:
      * Auto-Approve: p_wrong <= 0.05 and rules satisfied
      * Ask More Proof: 0.05 < p_wrong <= 0.30
      * Human Officer Review: p_wrong > 0.30 (The system never auto-rejects!)
    """
    case = _CASES_DB.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Task 3: Point-of-use consent check when helper initiates case evaluation
    if current_user.role == RoleEnum.HELPER and case.helper_id == current_user.id:
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )

    if not component_scores:
        has_blurry = any(d.is_blurry for d in case.documents)
        has_tampered = any(d.is_tampered for d in case.documents)
        ocr_avg = sum(d.ocr_confidence for d in case.documents) / len(case.documents) if case.documents else 0.85

        component_scores = ComponentScores(
            identity=0.92,
            ocr=0.60 if has_blurry else ocr_avg,
            authenticity=0.45 if has_tampered else 0.95,
            rules_complete=0.95 if case.monthly_income <= 35000.0 else 0.40,
            scam_safety=0.98
        )

    missing_docs = []
    if not any(d.doc_type == "cnic_front" for d in case.documents):
        missing_docs.append("CNIC front photo")
    if not any(d.doc_type == "utility_bill" for d in case.documents):
        missing_docs.append("Recent electricity or gas utility bill")

    tamper_flags = ["Suspected document digital tampering"] if any(d.is_tampered for d in case.documents) else []

    case_dict = case.model_dump()
    decision = decision_engine.evaluate_case(
        case_id=case_id,
        case_data=case_dict,
        component_scores=component_scores,
        missing_docs=missing_docs,
        tamper_flags=tamper_flags
    )

    if decision.route == RouteDecision.AUTO_APPROVE:
        case.status = CaseStatus.APPROVED
    elif decision.route == RouteDecision.ASK_MORE_PROOF:
        case.status = CaseStatus.NEED_MORE_INFO
    else:
        case.status = CaseStatus.IN_REVIEW

    case.decision = decision
    _CASES_DB[case_id] = case

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action=f"DECISION_EVALUATED:{decision.route.value}",
        resource_id=case_id,
        details={
            "route": decision.route.value,
            "overall_confidence": decision.confidence,
            "rule_version": decision.rule_version,
            "approval_token_generated": bool(decision.approval_token)
        }
    )

    return decision


@router.get("/explain/{case_id}")
async def explain_decision(
    case_id: str,
    view: str = "citizen",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Returns dual-view explanation:
    - view='citizen': Simple Urdu + English explanation with icons for low-literacy users.
    - view='auditor': Complete parameter trace, rule version, component confidences, and audit hash.
    """
    case = _CASES_DB.get(case_id)
    if not case or not case.decision:
        raise HTTPException(status_code=404, detail="Case or decision not found. Please evaluate first.")

    # Task 3: Point-of-use consent check when helper accesses explanation
    if current_user.role == RoleEnum.HELPER:
        if case.helper_id != current_user.id:
            raise HTTPException(status_code=403, detail="Helper not assigned to this case")
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )

    if view == "auditor" and current_user.role in [RoleEnum.CITIZEN, RoleEnum.HELPER]:
        raise HTTPException(
            status_code=403,
            detail="Auditor view is restricted to Department Officers, Admins, and Auditors."
        )

    if view == "auditor":
        audit_entries = audit_log.get_entries(resource_id=case_id, limit=1)
        audit_hash = audit_entries[0].current_hash if audit_entries else "GENESIS_LINK"
        return ExplanationBuilder.build_auditor_view(case.decision, case.model_dump(), audit_hash)

    return ExplanationBuilder.build_citizen_view(case.decision)
