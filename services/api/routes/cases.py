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
from pydantic import BaseModel, Field

from services.api.engine.audit_log import audit_log
from services.api.engine.consent_gateway import consent_gateway
from services.api.security.rbac import get_current_user, require_officer, require_staff
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
        # Automatically grant baseline consent when citizen self-registers (Identity and Income needed for basic intake)
        # Note: DOCUMENTS consent is NOT auto-granted; citizen must explicitly authorize document processing.
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

    # Enforce DOCUMENTS consent scope at point of use for all actors
    consent_gateway.read_gateway(
        actor_id=current_user.id,
        actor_role=current_user.role,
        citizen_id=case.citizen_id,
        scope=ConsentScope.DOCUMENTS,
        acting_helper_id=current_user.id if current_user.role == RoleEnum.HELPER else None
    )

    # If helper is acting, also verify HELPER_ACTING scope
    if current_user.role == RoleEnum.HELPER:
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
    DEPRECATED & DISABLED (Security Rule P0):
    Direct single-request CNIC verification with caller-supplied second_approver_id
    is strictly prohibited by Maker-Checker / Four-Eyes security policy.
    All legacy CNIC corrections must use the two-phase workflow:
    1. POST /api/v1/cases/legacy-cnic/propose-correction (Maker step)
    2. POST /api/v1/cases/legacy-cnic/approve-correction (Independent Checker step)
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={
            "code": "ENDPOINT_DEPRECATED_MAKER_CHECKER_REQUIRED",
            "message": (
                "Direct single-request verification is disabled. A single user or caller-supplied "
                "approver ID cannot authorize CNIC corrections. You must submit a proposal via "
                "/legacy-cnic/propose-correction and have an independent supervisor approve it via "
                "/legacy-cnic/approve-correction."
            )
        }
    )


@router.post("/legacy-cnic/propose-correction", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def propose_legacy_cnic_correction(
    req: LegacyCNICProposalRequest,
    current_user: UserResponse = Depends(require_staff)
):
    """
    Maker Step: Verifying Officer physically inspects document and proposes a CNIC correction.
    Persists proposal in database table `legacy_cnic_proposals` with status PENDING_APPROVAL.
    Does NOT update the citizen's CNIC in the database yet.
    """
    from db.connection import SessionLocal
    from db.models import Citizen as DBCitizen
    from db.models import LegacyCnicProposal

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

        # Check for existing pending proposal for this citizen
        existing_pending = db_session.query(LegacyCnicProposal).filter_by(
            citizen_id=req.citizen_id,
            status="PENDING_APPROVAL"
        ).first()
        if existing_pending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DUPLICATE_PROPOSAL: A pending proposal ({existing_pending.id}) already exists for citizen {req.citizen_id}."
            )

        # Check document reference deduplication against approved proposals
        used_ref = db_session.query(LegacyCnicProposal).filter_by(
            physical_document_ref=req.physical_document_ref,
            status="APPROVED"
        ).first()
        if used_ref:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"REUSED_DOCUMENT_REFERENCE: Document reference '{req.physical_document_ref}' was already used in approval {used_ref.id}."
            )

        # Also check historical audit log for used document reference
        from db.models import AuditLog as DBAuditLog
        prior_audits = db_session.query(DBAuditLog).filter(
            DBAuditLog.action == "LEGACY_CNIC_MANUALLY_VERIFIED"
        ).all()
        for pa in prior_audits:
            if pa.details and pa.details.get("doc_ref") == req.physical_document_ref:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"REUSED_DOCUMENT_REFERENCE: Document reference '{req.physical_document_ref}' was already used in verification {pa.request_id}."
                )

        proposal_id = f"prop_{uuid.uuid4().hex[:10]}"
        now_dt = datetime.utcnow()
        db_proposal = LegacyCnicProposal(
            id=proposal_id,
            citizen_id=req.citizen_id,
            old_cnic=citizen.cnic,
            proposed_cnic=req.verified_cnic,
            maker_officer_id=current_user.id,
            maker_notes=req.caseworker_notes,
            physical_document_ref=req.physical_document_ref,
            status="PENDING_APPROVAL",
            created_at=now_dt
        )
        db_session.add(db_proposal)
        db_session.commit()

        masked_cnic = f"{req.verified_cnic[:5]}-*******-{req.verified_cnic[-1]}" if len(req.verified_cnic) >= 15 else f"{req.verified_cnic[:5]}*****{req.verified_cnic[-1]}"
        audit_log.append(
            actor_id=current_user.id,
            actor_role=current_user.role,
            action="LEGACY_CNIC_CORRECTION_PROPOSED",
            resource_id=req.citizen_id,
            details={
                "proposal_id": proposal_id,
                "maker_officer_id": current_user.id,
                "proposed_cnic_masked": masked_cnic,
                "doc_ref": req.physical_document_ref
            }
        )

        return {
            "status": "PROPOSED",
            "proposal_id": proposal_id,
            "citizen_id": req.citizen_id,
            "verified_cnic": req.verified_cnic,
            "maker_officer_id": current_user.id,
            "message": "Proposal created and persisted in database. Correction will NOT take effect until an independent supervisor approves."
        }


@router.post("/legacy-cnic/approve-correction", response_model=Dict[str, Any])
async def approve_legacy_cnic_correction(
    req: LegacyCNICApprovalRequest,
    current_user: UserResponse = Depends(require_staff)
):
    """
    Checker Step: Independent supervisor reviews physical evidence and approves the correction.
    Enforces Maker-Checker separation (current_user.id != maker_officer_id).
    Checker identity is strictly derived from the authenticated session (never caller-supplied).
    Only upon approval is the citizen record updated in PostgreSQL and recorded in the audit ledger.
    """
    from db.connection import SessionLocal
    from db.models import Citizen as DBCitizen
    from db.models import LegacyCnicProposal

    with SessionLocal() as db_session:
        proposal = db_session.query(LegacyCnicProposal).filter_by(id=req.proposal_id).first()
        if not proposal:
            raise HTTPException(status_code=404, detail="Correction proposal not found.")

        if proposal.status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal is already {proposal.status} and cannot be re-processed."
            )

        # Maker-Checker strict separation: Checker cannot be the Maker
        if proposal.maker_officer_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MAKER_CHECKER_SELF_APPROVAL_FORBIDDEN: Independent supervisor approval cannot be granted by the verifying officer who created the proposal."
            )

        if current_user.role not in [RoleEnum.OFFICER, RoleEnum.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="UNAUTHORIZED_CHECKER: Approving supervisor must hold an active Officer or Admin credential."
            )

        citizen = db_session.query(DBCitizen).filter_by(id=proposal.citizen_id).first()
        if not citizen:
            raise HTTPException(status_code=404, detail="Citizen record not found in database.")

        # Update citizen CNIC and proposal status atomically
        old_cnic = citizen.cnic
        citizen.cnic = proposal.proposed_cnic
        proposal.status = "APPROVED"
        proposal.checker_supervisor_id = current_user.id
        proposal.supervisor_notes = req.supervisor_notes
        proposal.approved_at = datetime.utcnow()
        db_session.commit()

        # Immutable audit ledger entry recording both Maker and Checker with masked CNIC
        masked_cnic = f"{proposal.proposed_cnic[:5]}-*******-{proposal.proposed_cnic[-1]}" if len(proposal.proposed_cnic) >= 15 else f"{proposal.proposed_cnic[:5]}*****{proposal.proposed_cnic[-1]}"
        try:
            audit_log.append(
                actor_id=current_user.id,
                actor_role=current_user.role,
                action="LEGACY_CNIC_MANUALLY_VERIFIED",
                resource_id=proposal.citizen_id,
                details={
                    "proposal_id": req.proposal_id,
                    "old_cnic": old_cnic,
                    "verified_cnic": proposal.proposed_cnic,
                    "verified_cnic_masked": masked_cnic,
                    "maker_officer_id": proposal.maker_officer_id,
                    "checker_supervisor_id": current_user.id,
                    "doc_ref": proposal.physical_document_ref,
                    "caseworker_notes": proposal.maker_notes,
                    "supervisor_notes": req.supervisor_notes
                }
            )
        except Exception as audit_err:
            # Fail closed: rollback citizen and proposal if audit log append fails
            with SessionLocal() as rollback_session:
                r_cit = rollback_session.query(DBCitizen).filter_by(id=proposal.citizen_id).first()
                if r_cit:
                    r_cit.cnic = old_cnic
                r_prop = rollback_session.query(LegacyCnicProposal).filter_by(id=proposal.id).first()
                if r_prop:
                    r_prop.status = "PENDING_APPROVAL"
                    r_prop.checker_supervisor_id = None
                    r_prop.approved_at = None
                rollback_session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Security failure: audit logging failed, approval action rolled back ({str(audit_err)})"
            )

        return {
            "status": "APPROVED",
            "proposal_id": req.proposal_id,
            "citizen_id": proposal.citizen_id,
            "old_cnic": old_cnic,
            "verified_cnic": proposal.proposed_cnic,
            "maker_officer_id": proposal.maker_officer_id,
            "checker_supervisor_id": current_user.id,
            "message": "Citizen legacy CNIC successfully approved via Maker-Checker workflow and committed to PostgreSQL."
        }
