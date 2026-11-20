"""
Granular Consent Management Endpoints.
Implements Hackathon Challenge 06: Consent and Take-Back.
Citizens can view, grant, and withdraw consent for specific scopes.
Consent withdrawal takes effect immediately and blocks further reads.
"""
from fastapi import APIRouter, Depends, HTTPException

from services.api.engine.consent_gateway import consent_gateway
from services.api.security.rbac import get_current_user
from services.shared.schemas import ConsentGrantRequest, ConsentRecord, ConsentWithdrawRequest, RoleEnum, UserResponse

router = APIRouter(prefix="/consent", tags=["Consent & Take-Back"])


@router.post("/grant", response_model=ConsentRecord)
async def grant_consent(
    req: ConsentGrantRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Citizen grants granular consent for a scope (identity, income, bills, helper_acting).
    """
    if current_user.role == RoleEnum.CITIZEN and current_user.id != req.citizen_id:
        raise HTTPException(status_code=403, detail="Cannot grant consent on behalf of another citizen.")

    record = consent_gateway.grant_consent(
        citizen_id=req.citizen_id,
        scope=req.scope,
        helper_id=req.helper_id,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    return record


@router.post("/withdraw", response_model=ConsentRecord)
async def withdraw_consent(
    req: ConsentWithdrawRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Citizen withdraws consent for a scope.
    Instantly blocks any future read attempts via the Consent Gateway (HTTP 403).
    """
    if current_user.role == RoleEnum.CITIZEN and current_user.id != req.citizen_id:
        raise HTTPException(status_code=403, detail="Cannot withdraw consent on behalf of another citizen.")

    record = consent_gateway.withdraw_consent(
        citizen_id=req.citizen_id,
        scope=req.scope,
        actor_id=current_user.id,
        actor_role=current_user.role
    )
    return record


@router.get("/status/{citizen_id}")
async def get_consent_status(
    citizen_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Displays 'Who Has My Data': lists all granted and revoked scopes for a citizen.
    """
    if current_user.role == RoleEnum.CITIZEN and current_user.id != citizen_id:
        raise HTTPException(status_code=403, detail="Cannot view consent status of another citizen.")

    consents = consent_gateway.get_citizen_consents(citizen_id)
    return {
        "citizen_id": citizen_id,
        "consents": consents
    }
