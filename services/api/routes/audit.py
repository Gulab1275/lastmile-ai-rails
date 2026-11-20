"""
Cryptographic Audit Ledger Endpoints.
Implements Hackathon Challenge 05: Explain and Audit.
Provides append-only hash-chained logs and cryptographic chain verification.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from services.api.engine.audit_log import audit_log
from services.api.security.rbac import require_officer_or_auditor
from services.shared.schemas import AuditChainVerificationResponse, AuditLogEntry, UserResponse

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Log"])


@router.get("/logs", response_model=List[AuditLogEntry])
async def list_audit_logs(
    resource_id: Optional[str] = Query(None, description="Filter by case ID, citizen ID, or rule ID"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserResponse = Depends(require_officer_or_auditor)
):
    """
    Inspects cryptographic audit trail.
    Restricted to Department Officers, Admins, and Auditors.
    """
    return audit_log.get_entries(resource_id=resource_id, actor_id=actor_id, limit=limit)


@router.get("/verify-chain", response_model=AuditChainVerificationResponse)
async def verify_audit_chain(
    current_user: UserResponse = Depends(require_officer_or_auditor)
):
    """
    Verifies the SHA-256 cryptographic chain from the genesis block to head.
    Proves that no record has been altered, deleted, or backdated.
    """
    return audit_log.verify_chain()
