"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from services.api.config import settings
from services.api.engine.audit_log import audit_log
from services.api.security.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_id,
    register_user,
)
from services.api.security.rbac import get_current_user
from services.shared.schemas import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """Registers a new citizen or user account."""
    new_user = register_user(user_in)
    audit_log.append(
        actor_id=new_user.id,
        actor_role=new_user.role,
        action="USER_REGISTERED",
        resource_id=new_user.id,
        details={"username": new_user.username, "role": new_user.role.value}
    )
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticates user and returns JWT access and refresh tokens.
    Pre-seeded Demo Accounts:
    - citizen_parveen / password123 (Citizen - Widow)
    - citizen_tariq / password123 (Citizen - Shopkeeper)
    - helper_shazia / password123 (Community Helper)
    - officer_aslam / password123 (Department Officer)
    - admin_ayesha / password123 (System Admin)
    - auditor_iqbal / password123 (Auditor)
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message_en": "Incorrect username or password.",
                "message_ur": "صارف کا نام یا پاس ورڈ غلط ہے۔"
            }
        )

    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id, user.username, user.role)

    audit_log.append(
        actor_id=user.id,
        actor_role=user.role,
        action="USER_LOGIN",
        resource_id=user.id,
        details={"username": user.username}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        user_id=user.id,
        username=user.username
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_payload: dict):
    """Exchanges a valid refresh token for a new access token."""
    refresh_tok = token_payload.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="Missing refresh_token field")

    decoded = decode_token(refresh_tok, expected_type="refresh")
    user = get_user_by_id(decoded.sub)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(user.id, user.username, user.role)
    new_refresh = create_refresh_token(user.id, user.username, user.role)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        user_id=user.id,
        username=user.username
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    return current_user
