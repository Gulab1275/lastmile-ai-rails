"""
Configuration settings for Rahbar API.
Loads environment variables safely with prototype-safe defaults.
"""
import json
import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://rahbar.duckdns.org",
    "https://rahbar-backend.duckdns.org",
    "https://rahbar-pwa.vercel.app",
]


def _get_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOWED_ORIGINS")
    if not raw:
        return DEFAULT_ALLOWED_ORIGINS
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(o) for o in parsed if str(o) != "*"]
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback to comma-separated list
    return [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    APP_NAME: str = "Rahbar"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "rahbar-super-secret-development-key-change-in-production-min32chars"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    ALLOWED_ORIGINS: List[str] = _get_allowed_origins()

    AUDIT_CHECKPOINT_KEY: Optional[str] = os.getenv("AUDIT_CHECKPOINT_KEY", None)

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "20/minute"

    MOCK_CHAOS_MODE: str = os.getenv("MOCK_CHAOS_MODE", "none")
    MOCK_CHAOS_LATENCY_MS: int = 1500




settings = Settings()
