"""
Public REST API Router for Rahbar.
Protected by X-API-Key header (require_api_key dependency).
Exposes ONLY safe, non-PII endpoints:
- POST /api/v1/public/scam-check
- POST /api/v1/public/ask (policy Q&A)
- GET  /api/v1/public/health
No citizen personal data is exposed here.
"""
from fastapi import APIRouter, Depends

from db.models import ApiKey
from services.ai.rag import ask_policy
from services.ai.scam import classify_message
from services.api.security.api_key import require_api_key
from services.shared.schemas import (
    PolicyAskRequest,
    PolicyAskResponse,
    ScamCheckRequest,
    ScamCheckResponse,
)

router = APIRouter(prefix="/public", tags=["Public API"])


@router.get("/health")
def public_health(api_key: ApiKey = Depends(require_api_key)):
    """Public health endpoint. Confirms valid API key and service availability."""
    return {
        "status": "healthy",
        "api_key_name": api_key.name,
        "key_prefix": api_key.key_prefix,
        "message": "Rahbar Public Rails API is operational",
    }


@router.post("/scam-check", response_model=ScamCheckResponse)
def public_scam_check(
    payload: ScamCheckRequest,
    api_key: ApiKey = Depends(require_api_key),
):
    """Public scam detection service for SMS and WhatsApp messages."""
    res = classify_message(payload.text)
    return ScamCheckResponse(
        label=res["label"],
        confidence=res["confidence"],
        reasons=res["reasons"],
    )


@router.post("/ask", response_model=PolicyAskResponse)
def public_ask_policy(
    payload: PolicyAskRequest,
    api_key: ApiKey = Depends(require_api_key),
):
    """Public policy Q&A service answering official relief guidelines."""
    res = ask_policy(payload.question)
    return PolicyAskResponse(
        answer=res["answer"],
        sources=res["sources"],
        retrieval_mode=res.get("retrieval_mode", "supabase_pgvector"),
        provider=res.get("provider", "groq"),
    )
