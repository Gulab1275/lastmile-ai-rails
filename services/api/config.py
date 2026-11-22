"""
Configuration settings for Rahbar API.
Loads environment variables safely with prototype-safe defaults.
"""
import json
import os
from typing import Any, List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://rahbar.duckdns.org",
    "https://rahbar-backend.duckdns.org",
    "https://rahbar-pwa.vercel.app",
    "https://lastmile-ai-rails.vercel.app",
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


def _get_validated_secret_key() -> str:
    key = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
    if not key or not key.strip():
        raise RuntimeError(
            "CRITICAL_SECURITY_ERROR: SECRET_KEY environment variable is required and cannot be empty. "
            "Predictable hardcoded defaults are disabled."
        )
    key = key.strip()
    if len(key) < 32:
        raise RuntimeError(
            f"CRITICAL_SECURITY_ERROR: SECRET_KEY must be at least 32 characters (got {len(key)}). "
            "Configure a cryptographically secure key."
        )
    app_env = os.getenv("APP_ENV", "development").lower()
    insecure_keys = {
        "rahbar-super-secret-development-key-change-in-production-min32chars",
        "secret",
        "changeme",
        "default-secret-key-do-not-use",
    }
    if app_env == "production" and key in insecure_keys:
        raise RuntimeError(
            "CRITICAL_SECURITY_ERROR: Insecure development SECRET_KEY detected in production environment. "
            "Production must use an independently generated random secret."
        )
    return key


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

    SECRET_KEY: str = Field(default_factory=_get_validated_secret_key)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    ALLOWED_ORIGINS: List[str] = _get_allowed_origins()

    APPROVAL_TOKEN_SECRET: Optional[str] = Field(default_factory=lambda: os.getenv("APPROVAL_TOKEN_SECRET", None))
    AUDIT_CHECKPOINT_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("AUDIT_CHECKPOINT_KEY", None))

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "20/minute"

    MOCK_CHAOS_MODE: str = os.getenv("MOCK_CHAOS_MODE", "none")
    MOCK_CHAOS_LATENCY_MS: int = 1500

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: Any) -> str:
        if not v or not str(v).strip():
            v = os.getenv("SECRET_KEY") or os.getenv("JWT_SECRET")
        if not v or not str(v).strip():
            raise ValueError(
                "CRITICAL_SECURITY_ERROR: SECRET_KEY environment variable is required and cannot be empty. "
                "Predictable hardcoded defaults are disabled."
            )
        v_str = str(v).strip()
        if len(v_str) < 32:
            raise ValueError(
                f"CRITICAL_SECURITY_ERROR: SECRET_KEY must be at least 32 characters (got {len(v_str)}). "
                "Configure a cryptographically secure key."
            )
        app_env = os.getenv("APP_ENV", "development").lower()
        insecure_keys = {
            "rahbar-super-secret-development-key-change-in-production-min32chars",
            "secret",
            "changeme",
            "default-secret-key-do-not-use",
        }
        if app_env == "production" and v_str in insecure_keys:
            raise ValueError(
                "CRITICAL_SECURITY_ERROR: Insecure development SECRET_KEY detected in production environment. "
                "Production must use an independently generated random secret."
            )
        return v_str

    @model_validator(mode="after")
    def validate_cryptographic_key_separation(self) -> "Settings":
        app_env = (self.APP_ENV or "development").lower()
        insecure_keys = {
            "rahbar-super-secret-development-key-change-in-production-min32chars",
            "secret",
            "changeme",
            "default-secret-key-do-not-use",
        }

        # Validate APPROVAL_TOKEN_SECRET if present
        if self.APPROVAL_TOKEN_SECRET is not None and str(self.APPROVAL_TOKEN_SECRET).strip():
            app_sec = str(self.APPROVAL_TOKEN_SECRET).strip()
            if len(app_sec) < 32:
                raise ValueError(
                    f"CRITICAL_SECURITY_ERROR: APPROVAL_TOKEN_SECRET must be at least 32 characters (got {len(app_sec)})."
                )
            if app_env == "production" and app_sec in insecure_keys:
                raise ValueError(
                    "CRITICAL_SECURITY_ERROR: Insecure development APPROVAL_TOKEN_SECRET detected in production."
                )
            if app_sec == self.SECRET_KEY:
                raise ValueError(
                    "CRITICAL_SECURITY_ERROR: Cryptographic key separation violation: "
                    "APPROVAL_TOKEN_SECRET cannot be identical to SECRET_KEY."
                )

        # Validate AUDIT_CHECKPOINT_KEY if present
        if self.AUDIT_CHECKPOINT_KEY is not None and str(self.AUDIT_CHECKPOINT_KEY).strip():
            chk_sec = str(self.AUDIT_CHECKPOINT_KEY).strip()
            if len(chk_sec) < 32:
                raise ValueError(
                    f"CRITICAL_SECURITY_ERROR: AUDIT_CHECKPOINT_KEY must be at least 32 characters (got {len(chk_sec)})."
                )
            if app_env == "production" and chk_sec in insecure_keys:
                raise ValueError(
                    "CRITICAL_SECURITY_ERROR: Insecure development AUDIT_CHECKPOINT_KEY detected in production."
                )
            if chk_sec == self.SECRET_KEY:
                raise ValueError(
                    "CRITICAL_SECURITY_ERROR: Cryptographic key separation violation: "
                    "AUDIT_CHECKPOINT_KEY cannot be identical to SECRET_KEY."
                )
            if (
                self.APPROVAL_TOKEN_SECRET is not None
                and chk_sec == str(self.APPROVAL_TOKEN_SECRET).strip()
            ):
                raise ValueError(
                    "CRITICAL_SECURITY_ERROR: Cryptographic key separation violation: "
                    "AUDIT_CHECKPOINT_KEY cannot be identical to APPROVAL_TOKEN_SECRET."
                )

        return self




settings = Settings()
