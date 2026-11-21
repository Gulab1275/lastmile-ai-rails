import hashlib
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from services.shared.schemas import CaseStatus, ConsentStatus, UserRole

from .connection import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())

# ============================================================================
# Users & Roles (Authentication & RBAC)
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.CITIZEN.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# Mock Citizens & Helpers
# ============================================================================

class Citizen(Base):
    __tablename__ = "citizens"

    id = Column(String, primary_key=True, default=generate_uuid)
    cnic = Column(String(15), unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    name_variants = Column(JSON, default=list)  # e.g. ["Muhammad Ali", "Mohd Ali", "M. Ali"]
    phone = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    household_size = Column(Integer, default=1)
    monthly_income = Column(Float, default=0.0)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consents = relationship("Consent", back_populates="citizen", cascade="all, delete-orphan")
    cases = relationship("Case", back_populates="citizen")

class Delegation(Base):
    """Community Helper acting on behalf of a citizen with explicit consent."""
    __tablename__ = "delegations"

    id = Column(String, primary_key=True, default=generate_uuid)
    helper_id = Column(String, ForeignKey("users.id"), nullable=False)
    citizen_id = Column(String, ForeignKey("citizens.id"), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# Consent Management (Challenge 06)
# ============================================================================

class Consent(Base):
    __tablename__ = "consents"

    id = Column(String, primary_key=True, default=generate_uuid)
    citizen_id = Column(String, ForeignKey("citizens.id"), nullable=False)
    grantee = Column(String, nullable=False)  # e.g. "helper", "system", "reviewer"
    scope = Column(String, nullable=False)    # identity, income, documents, phone
    status = Column(String, default=ConsentStatus.ACTIVE.value)
    reason = Column(String, nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    citizen = relationship("Citizen", back_populates="consents")

# ============================================================================
# Cases & Documents Lifecycle
# ============================================================================

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    citizen_id = Column(String, ForeignKey("citizens.id"), nullable=False)
    helper_id = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default=CaseStatus.DRAFT.value)
    claim_amount = Column(Float, nullable=False)
    form_data = Column(JSON, default=dict)  # extracted structured fields
    idempotency_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = relationship("Citizen", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    decision = relationship("Decision", back_populates="case", uselist=False)
    review_item = relationship("ReviewItem", back_populates="case", uselist=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    doc_type = Column(String, nullable=False)  # cnic_front, cnic_back, utility_bill
    file_path = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    blur_score = Column(Float, default=0.0)
    tamper_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")

# ============================================================================
# Decision Core & Immutable Rules Engine (Challenge 01, 02, 04)
# ============================================================================

class RuleVersion(Base):
    __tablename__ = "rule_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, unique=True, nullable=False)
    rule_name = Column(String, nullable=False)
    conditions = Column(JSON, nullable=False)  # list of condition objects
    author = Column(String, nullable=False)
    status = Column(String, default="active")  # draft, active, archived
    created_at = Column(DateTime, default=datetime.utcnow)

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("cases.id"), unique=True, nullable=False)
    route = Column(String, nullable=False)  # auto_approve, ask_more_proof, human_review
    confidence = Column(Float, nullable=False)
    component_scores = Column(JSON, nullable=False)
    rule_version_id = Column(Integer, ForeignKey("rule_versions.id"), nullable=False)
    reason_simple = Column(JSON, nullable=False)   # {"en": "...", "ur": "..."}
    auditor_trace = Column(JSON, nullable=False)   # full execution trace
    approval_token = Column(String, nullable=True) # required for disbursement
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="decision")


# ============================================================================
# API Keys (Security)
# ============================================================================

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    # Store only the prefix (e.g., "rk_demo_") to display; the full key is never persisted.
    key_prefix = Column(String(12), nullable=False, index=True)
    # SHA‑256 hash of the full key (hex string).
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    # Owner (admin) user reference – optional if you want to track who created it.
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships (optional, useful for audit logs)
    owner = relationship("User", backref="api_keys", foreign_keys=[owner_user_id])

    def is_active(self) -> bool:
        return self.revoked_at is None

# End of file
# ============================================================================
# Review Items (Officer Queue)
# ============================================================================

class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("cases.id"), unique=True, nullable=False)
    priority = Column(Integer, default=1)  # 1 (high), 2 (med), 3 (low)
    confidence = Column(Float, nullable=False)
    assigned_officer_id = Column(String, ForeignKey("users.id"), nullable=True)
    handoff_packet = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    officer_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="review_item")

# ============================================================================
# Cryptographic Hash-Chained Audit Log (Challenge 05, 06)
# ============================================================================

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prev_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False)
    result = Column(String, nullable=False)
    request_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def create_entry(cls, session, actor: str, action: str, target: str, result: str, request_id: str):
        last_entry = session.query(cls).order_by(cls.id.desc()).first()
        prev_hash = last_entry.current_hash if last_entry else "0" * 64

        now = datetime.utcnow().isoformat()
        payload = f"{prev_hash}|{actor}|{action}|{target}|{result}|{request_id}|{now}"
        current_hash = hashlib.sha256(payload.encode()).hexdigest()

        entry = cls(
            prev_hash=prev_hash,
            current_hash=current_hash,
            actor=actor,
            action=action,
            target=target,
            result=result,
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        session.add(entry)
        session.commit()
        return entry

# ============================================================================
# Scam Messages, Policy Chunks (RAG) & Evals
# ============================================================================

class ScamMessage(Base):
    __tablename__ = "scam_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    message_text = Column(Text, nullable=False)
    label = Column(String, nullable=False)  # scam, legit, unsure
    confidence = Column(Float, nullable=False)
    reasons = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_name = Column(String, nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)  # float array
    created_at = Column(DateTime, default=datetime.utcnow)

class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
