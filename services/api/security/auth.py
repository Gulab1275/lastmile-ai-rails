"""
Authentication, Password Hashing (Argon2), and JWT Token Management.
Pre-seeded with demo accounts for all 5 roles for instant prototype evaluation:
- Citizen (Widow: Parveen Bibi)
- Citizen (Shopkeeper: Tariq)
- Helper (Shazia - managing 40 families)
- Department Officer (Aslam)
- Admin (Ayesha)
- Auditor (Iqbal)
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from services.api.config import settings
from services.shared.schemas import (
    RoleEnum,
    TokenPayload,
    UserCreate,
    UserResponse,
)

ph = PasswordHasher()


# In-memory user store for mock prototype
# In production with Supabase, Naresh's DB models connect here
_USERS_DB: Dict[str, Dict[str, Any]] = {}
_USERS_BY_USERNAME: Dict[str, str] = {}


def hash_password(password: str) -> str:
    """Hashes password with Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password using Argon2id."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: str, username: str, role: RoleEnum) -> str:
    """Generates short-lived JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "type": "access",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str, username: str, role: RoleEnum) -> str:
    """Generates longer-lived JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> TokenPayload:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        return TokenPayload(
            sub=payload["sub"],
            username=payload["username"],
            role=RoleEnum(payload["role"]),
            exp=payload["exp"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please refresh your session."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials."
        )


def register_user(user_in: UserCreate) -> UserResponse:
    """Registers a new user in the prototype store."""
    if user_in.username.lower() in _USERS_BY_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already registered."
        )

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    hashed = hash_password(user_in.password)
    now = datetime.utcnow()

    user_record = {
        "id": user_id,
        "username": user_in.username.lower(),
        "full_name": user_in.full_name,
        "role": user_in.role,
        "phone": user_in.phone,
        "cnic": user_in.cnic,
        "hashed_password": hashed,
        "is_active": True,
        "created_at": now
    }

    _USERS_DB[user_id] = user_record
    _USERS_BY_USERNAME[user_in.username.lower()] = user_id

    # Dual persistence to Supabase Postgres
    try:
        from db.connection import SessionLocal
        from db.models import User as DBUser
        with SessionLocal() as db_session:
            db_u = db_session.query(DBUser).filter_by(email=user_in.username.lower()).first()
            if not db_u:
                db_u = DBUser(
                    id=user_id,
                    email=user_in.username.lower(),
                    password_hash=hashed,
                    full_name=user_in.full_name,
                    role=user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role),
                    is_active=True
                )
                db_session.add(db_u)
                db_session.commit()
    except Exception:
        pass

    return UserResponse(
        id=user_id,
        username=user_record["username"],
        full_name=user_record["full_name"],
        role=user_record["role"],
        phone=user_record["phone"],
        cnic=user_record["cnic"],
        is_active=True,
        created_at=now
    )


def authenticate_user(username: str, password: str) -> Optional[UserResponse]:
    """Authenticates username and password."""
    user_id = _USERS_BY_USERNAME.get(username.lower())
    if not user_id:
        return None
    user_record = _USERS_DB.get(user_id)
    if not user_record or not user_record["is_active"]:
        return None
    if not verify_password(password, user_record["hashed_password"]):
        return None

    return UserResponse(
        id=user_record["id"],
        username=user_record["username"],
        full_name=user_record["full_name"],
        role=user_record["role"],
        phone=user_record["phone"],
        cnic=user_record["cnic"],
        is_active=user_record["is_active"],
        created_at=user_record["created_at"]
    )


def get_user_by_id(user_id: str) -> Optional[UserResponse]:
    """Retrieves user by ID."""
    u = _USERS_DB.get(user_id)
    if not u:
        return None
    return UserResponse(
        id=u["id"],
        username=u["username"],
        full_name=u["full_name"],
        role=u["role"],
        phone=u["phone"],
        cnic=u["cnic"],
        is_active=u["is_active"],
        created_at=u["created_at"]
    )


# Seed initial demo accounts for the 5 hackathon roles
def _seed_demo_accounts():
    demo_users = [
        UserCreate(
            username="citizen_parveen",
            password="password123",
            full_name="Parveen Bibi (Widow)",
            role=RoleEnum.CITIZEN,
            phone="0300-1234567",
            cnic="42101-1234567-1"
        ),
        UserCreate(
            username="citizen_tariq",
            password="password123",
            full_name="Mohammad Tariq (Shopkeeper)",
            role=RoleEnum.CITIZEN,
            phone="0312-7654321",
            cnic="42101-7654321-2"
        ),
        UserCreate(
            username="helper_shazia",
            password="password123",
            full_name="Shazia Akram (Community Helper)",
            role=RoleEnum.HELPER,
            phone="0333-5551234",
            cnic="42101-9998887-3"
        ),
        UserCreate(
            username="officer_aslam",
            password="password123",
            full_name="Aslam Khan (Department Officer)",
            role=RoleEnum.OFFICER,
            phone="0345-8889900",
            cnic="42201-1122334-4"
        ),
        UserCreate(
            username="admin_ayesha",
            password="password123",
            full_name="Ayesha Siddiqui (System Admin)",
            role=RoleEnum.ADMIN,
            phone="0321-4455667",
            cnic="42101-3344556-5"
        ),
        UserCreate(
            username="auditor_iqbal",
            password="password123",
            full_name="Iqbal Memon (Compliance Auditor)",
            role=RoleEnum.AUDITOR,
            phone="0301-7788990",
            cnic="42101-7788990-6"
        ),
    ]

    for u in demo_users:
        if u.username not in _USERS_BY_USERNAME:
            register_user(u)


_seed_demo_accounts()
