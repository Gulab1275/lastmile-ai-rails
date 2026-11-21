# API‑Key admin routes
# -------------------------------------------------
# Provides endpoints for admins to create, list and revoke API keys.
# All routes are protected by the existing JWT auth system (admin role).
# -------------------------------------------------
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from db.models import ApiKey, AuditLog, User
from services.api.security.api_key import create_api_key
from services.api.security.rbac import require_admin


class ApiKeyCreate(BaseModel):
    name: str


router = APIRouter(prefix="/admin/api-keys", tags=["admin", "api-keys"])


@router.post("", response_model=dict)
async def create_key(
    payload: ApiKeyCreate = Body(None),
    name: str | None = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Create a new API key.
    Returns the plaintext key (only shown once).
    """
    key_name = payload.name if payload and payload.name else name
    if not key_name:
        raise HTTPException(status_code=400, detail="Key name is required")

    api_key_obj = create_api_key(db, name=key_name, owner_user_id=admin_user.id)
    plaintext = getattr(api_key_obj, "_plain", None)
    if not plaintext:
        raise HTTPException(status_code=500, detail="Failed to generate API key")
    return {"id": api_key_obj.id, "name": api_key_obj.name, "key": plaintext}


@router.get("", response_model=list[dict])
async def list_keys(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """List all API keys (masked). Plaintext key is never returned."""
    keys = db.query(ApiKey).filter(ApiKey.owner_user_id == admin_user.id).all()
    result = []
    for k in keys:
        masked = f"{k.key_prefix}{'*' * 24}"
        result.append({
            "id": k.id,
            "name": k.name,
            "prefix": k.key_prefix,
            "masked_key": masked,
            "created_at": k.created_at,
            "revoked_at": k.revoked_at,
            "last_used_at": k.last_used_at,
        })
    return result


@router.post("/{key_id}/revoke", response_model=dict)
async def revoke_key(
    key_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Revoke an existing API key."""
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.owner_user_id == admin_user.id)
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    if api_key.revoked_at:
        raise HTTPException(status_code=400, detail="API key already revoked")

    api_key.revoked_at = datetime.utcnow()
    db.add(api_key)
    db.commit()

    AuditLog.create_entry(
        session=db,
        actor=admin_user.username or admin_user.id,
        action="api_key_revoked",
        target="api_key",
        result="success",
        request_id="unknown",
    )

    return {"status": "revoked", "id": api_key.id}
