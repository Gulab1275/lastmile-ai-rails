"""
Server-side Role-Based Access Control (RBAC).
Enforces that unauthorized roles are rejected with HTTP 403 Forbidden.
Example: Citizens attempting to access Officer review queues receive 403.
"""
from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.api.security.auth import decode_token, get_user_by_id
from services.shared.schemas import RoleEnum, TokenPayload, UserResponse

security_scheme = HTTPBearer(auto_error=True)


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> TokenPayload:
    """Extracts and verifies JWT token from Authorization header."""
    token = credentials.credentials
    return decode_token(token, expected_type="access")


async def get_current_user(
    payload: TokenPayload = Depends(get_current_user_payload)
) -> UserResponse:
    """Retrieves full current user from token subject."""
    user = get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists or is inactive."
        )
    return user


def require_roles(allowed_roles: List[RoleEnum]) -> Callable:
    """
    Dependency factory that restricts an endpoint to specific roles.
    Returns HTTP 403 Forbidden if user's role is not authorized.
    """
    async def role_checker(
        current_user: UserResponse = Depends(get_current_user)
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            allowed_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "RBAC_FORBIDDEN",
                    "message_en": f"Access denied. Required roles: {allowed_names}. Your role: '{current_user.role.value}'.",
                    "message_ur": f"رسائی مسترد کر دی گئی ہے۔ آپ کے پاس اس عمل کا اختیار ({current_user.role.value}) نہیں ہے۔",
                    "required_roles": allowed_names,
                    "user_role": current_user.role.value
                }
            )
        return current_user

    return role_checker


# Convenient pre-configured role dependencies
require_citizen = require_roles([RoleEnum.CITIZEN])
require_helper = require_roles([RoleEnum.HELPER])
require_officer = require_roles([RoleEnum.OFFICER])
require_admin = require_roles([RoleEnum.ADMIN])
require_auditor = require_roles([RoleEnum.AUDITOR])

# Multi-role dependencies
require_staff = require_roles([RoleEnum.OFFICER, RoleEnum.ADMIN])
require_officer_or_auditor = require_roles([RoleEnum.OFFICER, RoleEnum.ADMIN, RoleEnum.AUDITOR])
require_citizen_or_helper = require_roles([RoleEnum.CITIZEN, RoleEnum.HELPER])
