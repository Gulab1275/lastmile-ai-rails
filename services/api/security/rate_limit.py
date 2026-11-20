"""
Rate Limiting & Safety with SlowAPI.
Protects endpoints and downstream LLM models from exhaustion.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def get_client_identifier(request: Request) -> str:
    """
    Identifies client by API Key if present, otherwise by client IP.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    return get_remote_address(request)


limiter = Limiter(key_func=get_client_identifier)


def rate_limit_custom_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Returns bilingual HTTP 429 response on rate limit violation."""
    return JSONResponse(
        status_code=429,
        content={
            "code": "RATE_LIMIT_EXCEEDED",
            "message_en": "Too many requests. Please slow down and try again shortly.",
            "message_ur": "بہت زیادہ درخواستیں بھیجی گئیں۔ برائے مہربانی کچھ دیر بعد دوبارہ کوشش کریں۔",
            "details": {"limit": str(exc.detail)}
        }
    )
