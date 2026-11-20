"""
Configuration settings for Rahbar API.
Loads environment variables safely with prototype-safe defaults.
"""
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://rahbar.duckdns.org",
        "https://rahbar-pwa.vercel.app",
        "*"
    ]

    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "20/minute"

    MOCK_CHAOS_MODE: str = os.getenv("MOCK_CHAOS_MODE", "none")
    MOCK_CHAOS_LATENCY_MS: int = 1500

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
