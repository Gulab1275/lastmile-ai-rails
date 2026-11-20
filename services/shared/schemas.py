"""
Frozen Shared Pydantic Schemas for Rahbar.
Contract between Mahandar (API/Backend), Naresh (AI/DB), and Gulab (Frontend).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==========================================
# 1. Enums
# ==========================================

class RoleEnum(str, Enum):
    CITIZEN = "citizen"
    HELPER = "helper"
    OFFICER = "officer"
    ADMIN = "admin"
    AUDITOR = "auditor"


class RouteDecision(str, Enum):
    AUTO_APPROVE = "auto_approve"
    ASK_MORE_PROOF = "ask_more_proof"
    HUMAN_REVIEW = "human_review"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEED_MORE_INFO = "need_more_info"


class BenefitType(str, Enum):
    RELIEF_CASH_GRANT = "relief_cash_grant"
    RATION_SUBSIDY = "ration_subsidy"
    UTILITY_RELIEF = "utility_relief"


class ConsentScope(str, Enum):
    IDENTITY = "identity"
    INCOME = "income"
    BILLS = "bills"
    HELPER_ACTING = "helper_acting"


class ConsentAction(str, Enum):
    GRANT = "grant"
    WITHDRAW = "withdraw"
    CORRECT = "correct"


class ChaosMode(str, Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    STATUS_500 = "500"
    SLOW = "slow"
    BAD_DATA = "bad_data"


# ==========================================
# 2. Decision & AI Schemas (PRD Core Contract)
# ==========================================

class ComponentScores(BaseModel):
    identity: float = Field(..., ge=0.0, le=1.0, description="Identity match confidence")
    ocr: float = Field(..., ge=0.0, le=1.0, description="OCR extraction confidence")
    authenticity: float = Field(..., ge=0.0, le=1.0, description="Document authenticity / tamper score")
    rules_complete: float = Field(..., ge=0.0, le=1.0, description="Rule requirement completeness")
    scam_safety: float = Field(..., ge=0.0, le=1.0, description="Scam absence confidence (1.0 = safe)")


class ReasonSimple(BaseModel):
    en: str = Field(..., description="Plain-English simple explanation for the user")
    ur: str = Field(..., description="Plain-Urdu simple explanation for the user")


class DecisionResponse(BaseModel):
    case_id: str
    route: RouteDecision
    confidence: float = Field(..., ge=0.0, le=1.0, description="Weakest link confidence = min(components)")
    components: ComponentScores
    missing: List[str] = Field(default_factory=list, description="Missing or blurry documents/fields")
    reason_simple: ReasonSimple
    rule_version: int
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    approval_token: Optional[str] = Field(None, description="Cryptographic token required for gated disbursement")


class ErrorResponse(BaseModel):
    code: str
    message_en: str
    message_ur: str
    details: Optional[Dict[str, Any]] = None


# ==========================================
# 3. Authentication & User Schemas
# ==========================================

class UserBase(BaseModel):
    username: str
    full_name: str
    role: RoleEnum
    phone: Optional[str] = None
    cnic: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: RoleEnum
    user_id: str
    username: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    username: str
    role: RoleEnum
    exp: int


class UserResponse(UserBase):
    id: str
    is_active: bool = True
    created_at: datetime


# ==========================================
# 4. Case & Intake Schemas
# ==========================================

class DocumentAttachment(BaseModel):
    doc_id: str
    doc_type: str = Field(..., description="cnic_front, cnic_back, utility_bill, income_affidavit")
    file_name: str
    file_url: str
    ocr_confidence: float = 1.0
    is_blurry: bool = False
    is_tampered: bool = False
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class CaseCreate(BaseModel):
    citizen_name: str
    cnic: str = Field(..., description="13-digit Pakistani CNIC format (e.g. 42101-1234567-1 or 4210112345671)")
    phone: str
    household_size: int = Field(..., ge=1)
    monthly_income: float = Field(..., ge=0.0)
    benefit_type: BenefitType = BenefitType.RELIEF_CASH_GRANT
    requested_amount: float = Field(12000.0, ge=0.0)
    address: Optional[str] = None
    helper_id: Optional[str] = None
    notes: Optional[str] = None


class CaseUpdate(BaseModel):
    citizen_name: Optional[str] = None
    household_size: Optional[int] = None
    monthly_income: Optional[float] = None
    status: Optional[CaseStatus] = None
    notes: Optional[str] = None


class CaseResponse(BaseModel):
    id: str
    citizen_id: str
    citizen_name: str
    cnic: str
    phone: str
    household_size: int
    monthly_income: float
    benefit_type: BenefitType
    requested_amount: float
    status: CaseStatus
    helper_id: Optional[str] = None
    documents: List[DocumentAttachment] = Field(default_factory=list)
    decision: Optional[DecisionResponse] = None
    officer_notes: Optional[str] = None
    disbursement_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 5. Granular Consent Schemas
# ==========================================

class ConsentRecord(BaseModel):
    id: str
    citizen_id: str
    scope: ConsentScope
    granted: bool
    granted_to_helper_id: Optional[str] = None
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    audit_hash: str


class ConsentGrantRequest(BaseModel):
    citizen_id: str
    scope: ConsentScope
    helper_id: Optional[str] = None


class ConsentWithdrawRequest(BaseModel):
    citizen_id: str
    scope: ConsentScope


class ConsentCheckResponse(BaseModel):
    citizen_id: str
    scope: ConsentScope
    allowed: bool
    granted_at: Optional[datetime] = None
    active_helper_id: Optional[str] = None


# ==========================================
# 6. Versioned Rules Engine Schemas
# ==========================================

class RuleCondition(BaseModel):
    field: str
    operator: str = Field(..., description="lte, gte, eq, ne, in, not_in")
    value: Any
    description_en: str
    description_ur: str


class RuleSet(BaseModel):
    version: int
    name: str
    max_monthly_income: float = 35000.0
    min_household_size: int = 1
    max_auto_approve_amount: float = 15000.0
    requires_valid_cnic: bool = True
    requires_utility_bill: bool = True
    max_wrong_prob_auto_approve: float = 0.05
    max_wrong_prob_ask_proof: float = 0.30
    custom_conditions: List[RuleCondition] = Field(default_factory=list)
    created_by: str = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class RuleVersionResponse(BaseModel):
    version: int
    name: str
    is_active: bool
    rule_set: RuleSet
    created_at: datetime


class RuleEvaluationTrace(BaseModel):
    rule_name: str
    rule_version: int
    condition_results: List[Dict[str, Any]]
    passed_all: bool
    failed_conditions: List[str] = Field(default_factory=list)


# ==========================================
# 7. Officer Review & Handoff Schemas
# ==========================================

class HandoffPacket(BaseModel):
    case_id: str
    priority_score: float = Field(..., description="Priority score (0.0 to 10.0), higher = urgent review")
    overall_confidence: float
    component_breakdown: ComponentScores
    flags: List[str] = Field(default_factory=list, description="Reason flags triggering human review")
    rule_trace: RuleEvaluationTrace
    suggested_action: str
    citizen_summary: Dict[str, Any]


class ReviewQueueItem(BaseModel):
    case_id: str
    citizen_name: str
    cnic: str
    requested_amount: float
    benefit_type: BenefitType
    confidence: float
    priority_score: float
    status: CaseStatus
    handoff_packet: HandoffPacket
    submitted_at: datetime


class ReviewDecisionRequest(BaseModel):
    decision: RouteDecision  # auto_approve, ask_more_proof, human_review (or reject)
    approved: bool
    mandatory_officer_notes: str = Field(..., min_length=10, description="Mandatory audit notes justifying decision")
    override_reason: Optional[str] = None


# ==========================================
# 8. Mock DPI Rail Schemas
# ==========================================

class MockNADRARequest(BaseModel):
    cnic: str
    full_name: str
    father_husband_name: Optional[str] = None
    date_of_birth: Optional[str] = None


class MockNADRAResponse(BaseModel):
    matched: bool
    match_score: float = Field(..., ge=0.0, le=1.0)
    canonical_cnic: str
    canonical_name: str
    family_head_cnic: Optional[str] = None
    deceased: bool = False
    status: str = "VERIFIED"
    latency_ms: int = 120


class MockRaastRequest(BaseModel):
    idempotency_key: str
    case_id: str
    receiver_iban_or_raast_id: str
    amount: float
    approval_token: str
    purpose: str = "RELIEF_GRANT"


class MockRaastResponse(BaseModel):
    success: bool
    transaction_id: str
    idempotency_key: str
    disbursed_amount: float
    settled_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "SETTLED"
    latency_ms: int = 250


class MockComplaintRequest(BaseModel):
    citizen_cnic: str
    phone: str
    category: str = Field(..., description="delay, scam_report, wrong_deduction, agent_misbehavior")
    description: str


class MockComplaintResponse(BaseModel):
    ticket_id: str
    citizen_cnic: str
    status: str = "LOGGED"
    assigned_queue: str
    expected_resolution_days: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# 9. Cryptographic Audit Log Schemas
# ==========================================

class AuditLogEntry(BaseModel):
    id: str
    prev_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str
    actor_role: RoleEnum
    action: str
    resource_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    current_hash: str


class AuditChainVerificationResponse(BaseModel):
    is_valid: bool
    total_records: int
    corrupted_at_index: Optional[int] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    head_hash: Optional[str] = None


# ==========================================
# 10. Digital Twin & Webhook Schemas
# ==========================================

class RuleSimulationRequest(BaseModel):
    draft_rule_set: RuleSet
    sample_size: int = 50


class RuleSimulationResponse(BaseModel):
    total_cases_simulated: int
    previous_rule_version: int
    draft_rule_version: int
    previous_approval_rate: float
    projected_approval_rate: float
    approval_rate_delta: float
    impact_summary: str
    affected_case_ids: List[str] = Field(default_factory=list)


class WebhookSubscription(BaseModel):
    id: str
    target_url: str
    event_types: List[str]
    is_active: bool = True
    secret: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WebhookEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
