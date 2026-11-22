"""
Granular Consent Management Endpoints.
Implements Hackathon Challenge 06: Consent and Take-Back.
Citizens can view, grant, and withdraw consent for specific scopes.
Consent withdrawal takes effect immediately and blocks further reads.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from services.api.engine.consent_gateway import consent_gateway
from services.api.security.rbac import get_current_user
from services.shared.schemas import (
    ConsentGrantRequest,
    ConsentRecord,
    ConsentScope,
    ConsentWithdrawRequest,
    RoleEnum,
    UserResponse,
)

router = APIRouter(prefix="/consent", tags=["Consent & Take-Back"])


@router.post("/grant", response_model=ConsentRecord)
async def grant_consent(
    req: ConsentGrantRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Citizen grants granular consent for a scope (identity, income, bills, helper_acting, documents).
    Security rules:
    - Only an authenticated citizen can grant consent for their own citizen ID.
    - Helpers, officers, administrators, and auditors are strictly forbidden (HTTP 403).
    - An authenticated citizen cannot grant consent for another citizen ID (cross-citizen forbidden).
    - Caller-supplied actor IDs or body parameters must never override the authenticated session identity.
    """
    if current_user.role != RoleEnum.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CONSENT_GRANT_FORBIDDEN",
                "message": f"Access denied: Only authenticated citizens can authorize consent. Role '{current_user.role.value}' is prohibited."
            }
        )
    if current_user.id != req.citizen_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CROSS_CITIZEN_CONSENT_FORBIDDEN",
                "message": f"Access denied: Citizen '{current_user.id}' cannot grant consent on behalf of citizen '{req.citizen_id}'."
            }
        )

    record = consent_gateway.grant_consent(
        citizen_id=current_user.id,
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
    Security rules:
    - Only an authenticated citizen can withdraw consent for their own citizen ID.
    - Helpers, officers, administrators, and auditors are strictly forbidden (HTTP 403).
    - An authenticated citizen cannot withdraw consent for another citizen ID (cross-citizen forbidden).
    """
    if current_user.role != RoleEnum.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CONSENT_WITHDRAW_FORBIDDEN",
                "message": f"Access denied: Only authenticated citizens can withdraw consent. Role '{current_user.role.value}' is prohibited."
            }
        )
    if current_user.id != req.citizen_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CROSS_CITIZEN_WITHDRAW_FORBIDDEN",
                "message": f"Access denied: Citizen '{current_user.id}' cannot withdraw consent on behalf of citizen '{req.citizen_id}'."
            }
        )

    record = consent_gateway.withdraw_consent(
        citizen_id=current_user.id,
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
    Security rules:
    - Citizens can view their own consent status.
    - Helpers can view ONLY IF they hold active HELPER_ACTING consent for this citizen.
    - Other citizens, unauthorized helpers, officers, or admins without active consent are blocked (HTTP 403).
    - Auditors can view consent records for compliance verification without personal disclosure.
    """
    if current_user.role == RoleEnum.CITIZEN:
        if current_user.id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view consent status of another citizen."
            )
    elif current_user.role == RoleEnum.HELPER:
        if not consent_gateway.check_consent(citizen_id, ConsentScope.HELPER_ACTING, acting_helper_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Helper lacks active delegation consent for this citizen."
            )
    elif current_user.role == RoleEnum.AUDITOR:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Role '{current_user.role.value}' is not authorized to view citizen consent status."
        )

    consents = consent_gateway.get_citizen_consents(citizen_id)
    return {
        "citizen_id": citizen_id,
        "consents": consents
    }
