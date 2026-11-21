"""
Main FastAPI Application for Rahbar.
The Last Mile: AI on Public Rails (Coder's Cup '26).
Team: Mahandar (Backend Lead & AWS Infra), Naresh (Agents & DB), Gulab (Frontend & PWA).
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from services.api.config import settings
from services.api.routes.admin.api_keys import router as admin_api_keys_router
from services.api.routes.ai import router as ai_router
from services.api.routes.audit import router as audit_router
from services.api.routes.auth import router as auth_router
from services.api.routes.cases import router as cases_router
from services.api.routes.consent import router as consent_router
from services.api.routes.decision import router as decision_router
from services.api.routes.digital_twin import router as digital_twin_router
from services.api.routes.health import router as health_router
from services.api.routes.mock_routes import router as mock_router
from services.api.routes.public import router as public_router
from services.api.routes.review import router as review_router
from services.api.routes.rules import router as rules_router
from services.api.routes.webhooks import router as webhooks_router
from services.api.security.rate_limit import limiter, rate_limit_custom_handler

app = FastAPI(
    title="Rahbar API Gateway",
    description=(
        "Production-grade Digital Public Infrastructure (DPI) API Gateway for Rahbar.\n"
        "Built for Coder's Cup '26 Hackathon.\n"
        "Features: JWT/RBAC, Versioned Rules Engine, Weakest-Link Decision Engine, "
        "Consent Gateway, Cryptographic SHA-256 Audit Hash Chain, and Mock DPI Rails with Chaos Mode."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 1. SlowAPI Rate Limiting State & Error Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_custom_handler)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include Routers under API_V1_STR
api_prefix = settings.API_V1_STR

app.include_router(health_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)
app.include_router(cases_router, prefix=api_prefix)
app.include_router(decision_router, prefix=api_prefix)
app.include_router(review_router, prefix=api_prefix)
app.include_router(rules_router, prefix=api_prefix)
app.include_router(consent_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)
app.include_router(mock_router, prefix=api_prefix)
app.include_router(digital_twin_router, prefix=api_prefix)
app.include_router(webhooks_router, prefix=api_prefix)
app.include_router(ai_router, prefix=api_prefix)
app.include_router(admin_api_keys_router, prefix=api_prefix)
app.include_router(public_router, prefix=api_prefix)

# 4. Mount Static Directory & Serve Web App
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/app", include_in_schema=False)
async def serve_app():
    """Serves the interactive single-page PWA web dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "PWA Web App not found"}


# Root convenience redirect or status
@app.get("/")
async def root():
    return {
        "message": "Rahbar API Gateway is running.",
        "app": "/app",
        "docs": "/docs",
        "health": f"{api_prefix}/health",
        "version": "1.0.0"
    }
