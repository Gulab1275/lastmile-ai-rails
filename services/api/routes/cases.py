"""
Case Intake and Management Routes.
Implements Hackathon Challenges:
- Citizen intake
- Helper managing 40 families
- Granular consent checks before data read
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.engine.audit_log import audit_log
from services.api.engine.consent_gateway import consent_gateway
from services.api.security.rbac import get_current_user
from services.shared.schemas import (
    CaseCreate,
    CaseResponse,
    CaseStatus,
    ConsentScope,
    DocumentAttachment,
    RoleEnum,
    UserResponse,
)

router = APIRouter(prefix="/cases", tags=["Case Management"])

# In-memory cases database
_CASES_DB: Dict[str, CaseResponse] = {}


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: CaseCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Creates a new relief grant claim.
    Citizens can create for themselves.
    Helpers can create for a family IF helper acting consent is given.
    """
    case_id = f"cas_{uuid.uuid4().hex[:10]}"
    citizen_id = current_user.id if current_user.role == RoleEnum.CITIZEN else (case_in.helper_id or current_user.id)
    helper_id = current_user.id if current_user.role == RoleEnum.HELPER else case_in.helper_id

    # If helper is submitting, verify helper acting consent
    if current_user.role == RoleEnum.HELPER:
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )

    now = datetime.utcnow()
    case_obj = CaseResponse(
        id=case_id,
        citizen_id=citizen_id,
        citizen_name=case_in.citizen_name,
        cnic=case_in.cnic,
        phone=case_in.phone,
        household_size=case_in.household_size,
        monthly_income=case_in.monthly_income,
        benefit_type=case_in.benefit_type,
        requested_amount=case_in.requested_amount,
        status=CaseStatus.DRAFT,
        helper_id=helper_id,
        documents=[],
        created_at=now,
        updated_at=now
    )

    _CASES_DB[case_id] = case_obj

    # Automatically grant baseline consent when citizen self-registers
    if current_user.role == RoleEnum.CITIZEN:
        consent_gateway.grant_consent(citizen_id, ConsentScope.IDENTITY, actor_id=current_user.id, actor_role=current_user.role)
        consent_gateway.grant_consent(citizen_id, ConsentScope.INCOME, actor_id=current_user.id, actor_role=current_user.role)

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="CASE_CREATED",
        resource_id=case_id,
        details={"citizen_name": case_in.citizen_name, "cnic": case_in.cnic, "amount": case_in.requested_amount}
    )

    return case_obj


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[CaseStatus] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Lists cases with role-based filtering:
    - Citizens: only their own cases.
    - Helpers: cases for families they manage.
    - Officers/Admins/Auditors: all cases.
    """
    all_cases = list(_CASES_DB.values())

    if current_user.role == RoleEnum.CITIZEN:
        cases = [c for c in all_cases if c.citizen_id == current_user.id]
    elif current_user.role == RoleEnum.HELPER:
        cases = [c for c in all_cases if c.helper_id == current_user.id]
    else:
        cases = all_cases

    if status_filter:
        cases = [c for c in cases if c.status == status_filter]

    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retrieves full case details.
    Enforces privacy: if helper views, verifies helper consent; if citizen views, must be owner.
    """
    case = _CASES_DB.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Access checks
    if current_user.role == RoleEnum.CITIZEN and case.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access cases of other citizens.")

    if current_user.role == RoleEnum.HELPER and case.helper_id == current_user.id:
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.IDENTITY,
            acting_helper_id=current_user.id
        )

    return case


@router.post("/{case_id}/documents", response_model=CaseResponse)
async def attach_document(
    case_id: str,
    doc: DocumentAttachment,
    current_user: UserResponse = Depends(get_current_user)
):
    """Attaches a verified or scanned document to the case."""
    case = _CASES_DB.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.documents.append(doc)
    case.updated_at = datetime.utcnow()
    _CASES_DB[case_id] = case

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="DOCUMENT_ATTACHED",
        resource_id=case_id,
        details={"doc_type": doc.doc_type, "ocr_confidence": doc.ocr_confidence, "is_blurry": doc.is_blurry}
    )

    return case


@router.post("/{case_id}/submit", response_model=CaseResponse)
async def submit_case(
    case_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Submits a draft case for evaluation."""
    case = _CASES_DB.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = CaseStatus.SUBMITTED
    case.updated_at = datetime.utcnow()
    _CASES_DB[case_id] = case

    audit_log.append(
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="CASE_SUBMITTED",
        resource_id=case_id,
        details={"citizen_id": case.citizen_id}
    )

    return case
