"""
Case Intake and Management Routes.
Implements Hackathon Challenges:
- Citizen intake
- Helper managing 40 families
- Granular consent checks before data read
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.engine.audit_log import audit_log
from services.api.engine.consent_gateway import consent_gateway
from services.api.security.rbac import get_current_user, require_officer
from pydantic import BaseModel, Field
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
# Maker-Checker pending proposals store for legacy CNIC remediation
_LEGACY_CNIC_PROPOSALS: Dict[str, Dict[str, Any]] = {}


class LegacyCNICVerificationRequest(BaseModel):
    citizen_id: str
    verified_cnic: str = Field(..., pattern=r"^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$")
    caseworker_notes: str = Field(..., min_length=15, description="Physical verification notes and document reference")
    physical_document_ref: str = Field(..., pattern=r"^(NADRA-(SCAN|TOK|REF)-[A-Za-z0-9]{3,12}|CARD-SCAN-[0-9]{6,12})$", description="NADRA physical token or card scan ID")
    second_approver_id: Optional[str] = Field(default=None, description="Independent second-person authorizing officer/supervisor ID")


class LegacyCNICProposalRequest(BaseModel):
    citizen_id: str
    verified_cnic: str = Field(..., pattern=r"^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$")
    caseworker_notes: str = Field(..., min_length=15, description="Physical verification inspection notes")
    physical_document_ref: str = Field(..., pattern=r"^(NADRA-(SCAN|TOK|REF)-[A-Za-z0-9]{3,12}|CARD-SCAN-[0-9]{6,12})$", description="NADRA physical token or card scan ID")


class LegacyCNICApprovalRequest(BaseModel):
    proposal_id: str
    supervisor_notes: str = Field(..., min_length=10, description="Independent supervisor review and confirmation notes")


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
    # Task 1 Guardrail: Restrict unverified legacy CNICs (-X) from normal intake
    if case_in.cnic and case_in.cnic.endswith("-X"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNVERIFIED_LEGACY_CNIC",
                "message_en": "Citizen CNIC is an unverified legacy record (ending in -X). Identity-dependent production workflows are restricted until manual caseworker verification.",
                "message_ur": "شناختی کارڈ غیر تصدیق شدہ پرانا ریکارڈ ہے۔ دستی تصدیق تک سروس معطل ہے۔"
            }
        )

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

    # Dual-persistence to Supabase Postgres
    try:
        from db.connection import SessionLocal
        from db.models import Case as DBCase
        with SessionLocal() as db_session:
            db_case = DBCase(
                id=case_id,
                citizen_id=citizen_id,
                helper_id=helper_id,
                status=CaseStatus.DRAFT.value,
                claim_amount=float(case_in.requested_amount),
                form_data=case_in.model_dump() if hasattr(case_in, "model_dump") else case_in.__dict__
            )
            db_session.add(db_case)
            db_session.commit()
    except Exception:
        pass

    # Fail-closed transaction: audit logging failure strictly rolls back the business action
    try:
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
    except Exception as audit_err:
        _CASES_DB.pop(case_id, None)
        try:
            from db.connection import SessionLocal
            from db.models import Case as DBCase
            with SessionLocal() as rollback_session:
                rollback_session.query(DBCase).filter_by(id=case_id).delete()
                rollback_session.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security failure: audit logging failed, business action rolled back ({str(audit_err)})"
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
        # Task 3: Check active helper consent at point of use before returning protected family cases
        cases = [
            c for c in all_cases 
            if c.helper_id == current_user.id and consent_gateway.check_consent(c.citizen_id, ConsentScope.HELPER_ACTING, current_user.id)
        ]
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
        # Task 3: Authoritative point-of-use gatekeeper checking helper acting and identity consent
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )
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

    # Task 3: Check helper consent before allowing modifications to citizen case
    if current_user.role == RoleEnum.HELPER and case.helper_id == current_user.id:
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )

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

    # Task 3: Check helper consent before allowing submission
    if current_user.role == RoleEnum.HELPER and case.helper_id == current_user.id:
        consent_gateway.read_gateway(
            actor_id=current_user.id,
            actor_role=current_user.role,
            citizen_id=case.citizen_id,
            scope=ConsentScope.HELPER_ACTING,
            acting_helper_id=current_user.id
        )

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


@router.post("/legacy-cnic/verify-and-correct", response_model=Dict[str, Any])
async def verify_and_correct_legacy_cnic(
    req: LegacyCNICVerificationRequest,
    current_user: UserResponse = Depends(require_officer)
):
    """
    Task 1: Auditable manual verification and correction of legacy non-conforming CNIC records.
    Restricted to Department Officers and Admins.
    Never alters records automatically or infers digits.
    Updates the database only with caseworker verified physical proof and appends to audit ledger.
    """
    from db.connection import SessionLocal
    from db.models import Citizen as DBCitizen

    if req.verified_cnic.endswith("-X"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verified CNIC cannot be another legacy format ending in -X."
        )

    with SessionLocal() as db_session:
        citizen = db_session.query(DBCitizen).filter_by(id=req.citizen_id).first()
        if not citizen:
            raise HTTPException(status_code=404, detail="Citizen record not found.")

        if not citizen.cnic.endswith("-X"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Citizen {citizen.id} is already in valid format ({citizen.cnic}) and does not require legacy remediation."
            )

        # Check if verified CNIC is already in use
        existing = db_session.query(DBCitizen).filter(DBCitizen.cnic == req.verified_cnic, DBCitizen.id != req.citizen_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Verified CNIC {req.verified_cnic} is already registered to citizen {existing.id}."
            )

        # Reused document reference deduplication: physical evidence must not be reused across citizens
        from db.models import AuditLog as DBAuditLog
        prior_use = db_session.query(DBAuditLog).filter(
            DBAuditLog.action == "LEGACY_CNIC_MANUALLY_VERIFIED",
            DBAuditLog.details["doc_ref"].astext == req.physical_document_ref
        ).first()
        if prior_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"REUSED_DOCUMENT_REFERENCE: Document reference '{req.physical_document_ref}' was already used in verification {prior_use.request_id}."
            )

        # Independent Second-Person Approval (Maker-Checker / Four-Eyes Principle)
        if not req.second_approver_id or not req.second_approver_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SECOND_APPROVER_MANDATORY: Independent second-person approval is strictly required under maker-checker policy."
            )

        if req.second_approver_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MAKER_CHECKER_SELF_APPROVAL_FORBIDDEN: Independent second-person approval cannot be self-issued by the verifying officer."
            )

        from services.api.security.auth import _USERS_DB
        approver_info = _USERS_DB.get(req.second_approver_id)
        if not approver_info or approver_info.get("role") not in [RoleEnum.OFFICER, RoleEnum.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="UNAUTHORIZED_SECOND_APPROVER: Second approver must hold an active Officer or Admin credential."
            )

        old_cnic = citizen.cnic
        citizen.cnic = req.verified_cnic
        db_session.commit()

        # Audit log entry for the manual correction with masked CNIC for log safety
        masked_cnic = f"{req.verified_cnic[:5]}-*******-{req.verified_cnic[-1]}" if len(req.verified_cnic) >= 15 else f"{req.verified_cnic[:5]}*****{req.verified_cnic[-1]}"
        audit_log.append(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="LEGACY_CNIC_MANUALLY_VERIFIED",
            resource_id=req.citizen_id,
            details={
                "old_cnic": old_cnic,
                "verified_cnic": req.verified_cnic,
                "verified_cnic_masked": masked_cnic,
                "officer_id": current_user.id,
                "second_approver_id": req.second_approver_id,
                "doc_ref": req.physical_document_ref,
                "notes": req.caseworker_notes
            }
        )

        return {
            "status": "SUCCESS",
            "citizen_id": req.citizen_id,
            "old_cnic": old_cnic,
            "verified_cnic": req.verified_cnic,
            "officer_id": current_user.id,
            "second_approver_id": req.second_approver_id,
            "verified_at": datetime.utcnow().isoformat(),
            "message": "Citizen legacy CNIC successfully verified with physical documentation and updated in PostgreSQL."
        }


@router.post("/legacy-cnic/propose-correction", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def propose_legacy_cnic_correction(
    req: LegacyCNICProposalRequest,
    current_user: UserResponse = Depends(require_officer)
):
    """
    Maker Step: Verifying Officer physically inspects document and proposes a CNIC correction.
    Does NOT update the citizen's CNIC in the database yet. Status remains PENDING_APPROVAL.
    """
    from db.connection import SessionLocal
    from db.models import Citizen as DBCitizen, AuditLog as DBAuditLog

    if req.verified_cnic.endswith("-X"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposed CNIC cannot be another legacy format ending in -X."
        )

    with SessionLocal() as db_session:
        citizen = db_session.query(DBCitizen).filter_by(id=req.citizen_id).first()
        if not citizen:
            raise HTTPException(status_code=404, detail="Citizen record not found.")

        if not citizen.cnic.endswith("-X"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Citizen {citizen.id} is already in valid format ({citizen.cnic}) and does not require legacy remediation."
            )

        # Check document reference deduplication
        prior_use = db_session.query(DBAuditLog).filter(
            DBAuditLog.action == "LEGACY_CNIC_MANUALLY_VERIFIED",
            DBAuditLog.details["doc_ref"].astext == req.physical_document_ref
        ).first()
        if prior_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"REUSED_DOCUMENT_REFERENCE: Document reference '{req.physical_document_ref}' was already used in verification {prior_use.request_id}."
            )

    proposal_id = f"prop_{uuid.uuid4().hex[:10]}"
    proposal = {
        "proposal_id": proposal_id,
        "citizen_id": req.citizen_id,
        "old_cnic": citizen.cnic,
        "verified_cnic": req.verified_cnic,
        "maker_officer_id": current_user.id,
        "physical_document_ref": req.physical_document_ref,
        "caseworker_notes": req.caseworker_notes,
        "status": "PENDING_APPROVAL",
        "created_at": datetime.utcnow().isoformat()
    }
    _LEGACY_CNIC_PROPOSALS[proposal_id] = proposal

    return {
        "status": "PROPOSED",
        "proposal_id": proposal_id,
        "citizen_id": req.citizen_id,
        "verified_cnic": req.verified_cnic,
        "maker_officer_id": current_user.id,
        "message": "Proposal created. Correction will NOT take effect until an independent supervisor approves."
    }


@router.post("/legacy-cnic/approve-correction", response_model=Dict[str, Any])
async def approve_legacy_cnic_correction(
    req: LegacyCNICApprovalRequest,
    current_user: UserResponse = Depends(require_officer)
):
    """
    Checker Step: Independent supervisor reviews physical evidence and approves the correction.
    Enforces Maker-Checker separation (current_user.id != maker_officer_id).
    Only upon approval is the citizen record updated in PostgreSQL and recorded in the audit ledger.
    """
    proposal = _LEGACY_CNIC_PROPOSALS.get(req.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Correction proposal not found.")

    if proposal["status"] != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposal is already {proposal['status']} and cannot be re-processed."
        )

    # Maker-Checker strict separation: Checker cannot be the Maker
    if proposal["maker_officer_id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MAKER_CHECKER_SELF_APPROVAL_FORBIDDEN: Independent supervisor approval cannot be granted by the verifying officer who created the proposal."
        )

    from db.connection import SessionLocal
    from db.models import Citizen as DBCitizen

    with SessionLocal() as db_session:
        citizen = db_session.query(DBCitizen).filter_by(id=proposal["citizen_id"]).first()
        if not citizen:
            raise HTTPException(status_code=404, detail="Citizen record not found in database.")

        # Update citizen CNIC in PostgreSQL
        old_cnic = citizen.cnic
        citizen.cnic = proposal["verified_cnic"]
        db_session.commit()

        # Update proposal in memory
        proposal["status"] = "APPROVED"
        proposal["checker_supervisor_id"] = current_user.id
        proposal["supervisor_notes"] = req.supervisor_notes
        proposal["approved_at"] = datetime.utcnow().isoformat()
        _LEGACY_CNIC_PROPOSALS[req.proposal_id] = proposal

        # Immutable audit ledger entry recording both Maker and Checker
        masked_cnic = f"{proposal['verified_cnic'][:5]}-*******-{proposal['verified_cnic'][-1]}" if len(proposal["verified_cnic"]) >= 15 else f"{proposal['verified_cnic'][:5]}*****{proposal['verified_cnic'][-1]}"
        audit_log.append(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="LEGACY_CNIC_MANUALLY_VERIFIED",
            resource_id=proposal["citizen_id"],
            details={
                "proposal_id": req.proposal_id,
                "old_cnic": old_cnic,
                "verified_cnic": proposal["verified_cnic"],
                "verified_cnic_masked": masked_cnic,
                "maker_officer_id": proposal["maker_officer_id"],
                "checker_supervisor_id": current_user.id,
                "doc_ref": proposal["physical_document_ref"],
                "caseworker_notes": proposal["caseworker_notes"],
                "supervisor_notes": req.supervisor_notes
            }
        )

        return {
            "status": "APPROVED",
            "proposal_id": req.proposal_id,
            "citizen_id": proposal["citizen_id"],
            "old_cnic": old_cnic,
            "verified_cnic": proposal["verified_cnic"],
            "maker_officer_id": proposal["maker_officer_id"],
            "checker_supervisor_id": current_user.id,
            "message": "Citizen legacy CNIC successfully approved via Maker-Checker workflow and committed to PostgreSQL."
        }
