"""
Department Officer Review Queue Endpoints.
Implements:
- Challenge 02: Saying 'I Am Not Sure' (routing low-confidence or high-risk cases to human officers with handoff packet)
- Mandatory officer review notes for approval/rejection
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.engine.audit_log import audit_log
from services.api.engine.decision_engine import decision_engine, generate_approval_token
from services.api.routes.cases import _CASES_DB
from services.api.security.rbac import require_officer
from services.shared.schemas import CaseResponse, CaseStatus, ReviewDecisionRequest, ReviewQueueItem, UserResponse

router = APIRouter(prefix="/review", tags=["Officer Review Queue"])


@router.get("/queue", response_model=List[ReviewQueueItem])
async def get_review_queue(
    current_user: UserResponse = Depends(require_officer)
):
    """
    Returns queue of cases requiring human review.
    Sorted by Priority Score (descending) and Confidence (ascending).
    Includes full Handoff Packet with case notes and reason flags.
    """
    queue_items: List[ReviewQueueItem] = []

    for case in _CASES_DB.values():
        if case.status in [CaseStatus.IN_REVIEW, CaseStatus.SUBMITTED]:
            if not case.decision:
                from services.shared.schemas import ComponentScores
                comp = ComponentScores(
                    identity=0.80,
                    ocr=0.70,
                    authenticity=0.85,
                    rules_complete=0.75,
                    scam_safety=0.90
                )
                decision = decision_engine.evaluate_case(case.id, case.model_dump(), comp)
            else:
                decision = case.decision

            handoff = decision_engine.build_handoff_packet(case.id, case.model_dump(), decision)

            queue_items.append(
                ReviewQueueItem(
                    case_id=case.id,
                    citizen_name=case.citizen_name,
                    cnic=case.cnic,
                    requested_amount=case.requested_amount,
                    benefit_type=case.benefit_type,
                    confidence=decision.confidence,
                    priority_score=handoff.priority_score,
                    status=case.status,
                    handoff_packet=handoff,
                    submitted_at=case.created_at
                )
            )

    queue_items.sort(key=lambda item: (-item.priority_score, item.confidence))
    return queue_items


@router.post("/{case_id}/decision", response_model=CaseResponse)
async def submit_officer_decision(
    case_id: str,
    review_req: ReviewDecisionRequest,
    current_user: UserResponse = Depends(require_officer)
):
    """
    Department Officer approves or rejects a claim.
    Mandatory audit requirement: Officer MUST provide written notes justifying the decision.
    If approved, generates a cryptographic approval token for gated payment release.
    """
    case = _CASES_DB.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if len(review_req.mandatory_officer_notes.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory officer notes must be at least 10 characters justifying the decision."
        )

    if review_req.approved:
        case.status = CaseStatus.APPROVED
        rule_version = case.decision.rule_version if case.decision else 1
        confidence = case.decision.confidence if case.decision else 0.90
        token = generate_approval_token(case.id, rule_version, confidence)
        if case.decision:
            case.decision.approval_token = token
    else:
        case.status = CaseStatus.REJECTED

    case.officer_notes = review_req.mandatory_officer_notes
    _CASES_DB[case_id] = case

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action=f"OFFICER_REVIEW_DECISION:{'APPROVED' if review_req.approved else 'REJECTED'}",
        resource_id=case_id,
        details={
            "officer_name": current_user.full_name,
            "approved": review_req.approved,
            "notes": review_req.mandatory_officer_notes,
            "override_reason": review_req.override_reason
        }
    )

    return case
