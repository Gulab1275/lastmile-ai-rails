# API‑key security utilities
# -------------------------------------------------
# This module provides:
#   * generation of a new API key (plaintext returned once)
#   * hashing of the key (SHA‑256) for storage
#   * FastAPI dependency that validates the X‑API‑Key header
#   * helper to retrieve the ApiKey ORM object (for audit / rate‑limit)
# -------------------------------------------------
import hashlib
import secrets
from datetime import datetime

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from db import get_db
from db.models import ApiKey, AuditLog

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_KEY_HEADER = "X-API-Key"
KEY_PREFIX = "rk_demo_"  # demo prefix (no real secret)
KEY_RANDOM_BYTES = 32  # 256‑bit entropy => ~43‑base64 chars; we truncate for readability

# ---------------------------------------------------------------------------
def _hash_key(key: str) -> str:
    """Return a hex SHA‑256 hash of the supplied key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_plaintext_key() -> str:
    """Create a new API key and return the *plaintext* version.
    The key is composed of the fixed prefix plus a url‑safe random token.
    Example: ``{KEY_PREFIX}AbCdEfGhIjKlMnOpQrStUvWxYz123456``
    """
    random_part = secrets.token_urlsafe(KEY_RANDOM_BYTES)
    return f"{KEY_PREFIX}{random_part}"


def create_api_key(
    db: Session,
    name: str,
    owner_user_id: str | None = None,
) -> ApiKey:
    """Persist a new ``ApiKey`` row and return the ORM instance.
    The plaintext key is **not** stored – only its hash and the prefix.
    """
    plaintext = generate_plaintext_key()
    key_hash = _hash_key(plaintext)
    prefix = plaintext[: len(KEY_PREFIX)]  # include the trailing underscore
    api_key = ApiKey(
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        owner_user_id=owner_user_id,
        created_at=datetime.utcnow(),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    # Attach the plaintext for the caller (will be used only once to return to admin)
    api_key._plain = plaintext  # type: ignore[attr-defined]
    # Audit log for key creation
    AuditLog.create_entry(
        session=db,
        actor=owner_user_id or "system",
        action="api_key_created",
        target="api_key",
        result="success",
        request_id="unknown",
    )
    return api_key


def _load_key_by_prefix_and_hash(db: Session, prefix: str, key_hash: str) -> ApiKey | None:
    return (
        db.query(ApiKey)
        .filter(ApiKey.key_prefix == prefix, ApiKey.key_hash == key_hash)
        .first()
    )


async def require_api_key(
    db: Session = Depends(get_db),
    api_key_header: str = Header(None, description="X-API-Key header for service access"), request: Request = Depends(),
) -> ApiKey:
    """FastAPI dependency that validates the API‑key header.
    Returns the ``ApiKey`` ORM object when valid; otherwise raises ``401``.
    """
    if not api_key_header:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    # Split prefix and secret – our format guarantees the prefix length
    prefix = api_key_header[: len(KEY_PREFIX)]
    secret = api_key_header[len(KEY_PREFIX) :]
    # Compute hash of the *full* key (prefix + secret)
    full_key = f"{prefix}{secret}"
    key_hash = _hash_key(full_key)
    api_key_obj = _load_key_by_prefix_and_hash(db, prefix, key_hash)
    if not api_key_obj or not api_key_obj.is_active():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API key")


    # Update last used timestamp (non‑blocking – commit happens later in request lifecycle)
    api_key_obj.last_used_at = datetime.utcnow()
    db.add(api_key_obj)
    db.commit()
    # Record successful usage in audit log (actor = key prefix, action = "api_key_used")
    AuditLog.create_entry(
        session=db,
        actor=api_key_obj.key_prefix,
        action="api_key_used",
        target="api",
        result="success",
        request_id=request.headers.get("X-Request-ID", "unknown"),
    )
    return api_key_obj

