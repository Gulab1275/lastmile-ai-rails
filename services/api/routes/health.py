"""
System Health & Telemetry Endpoint.
Provides comprehensive health telemetry, plus separate Kubernetes Liveness and Readiness probes.
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from services.api.engine.audit_log import audit_log
from services.api.engine.rules_engine import rules_engine

router = APIRouter(tags=["Health & Status"])

BOOT_TIME = datetime.utcnow()


@router.get("/health/liveness")
async def liveness_check():
    """
    Kubernetes / Container Liveness Probe.
    Returns 200 OK immediately if the web process is running.
    Never checks external dependencies (no DB, no network calls).
    """
    return {
        "status": "alive",
        "service": "Rahbar API Gateway",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/readiness")
async def readiness_check():
    """
    Kubernetes / Container Readiness Probe.
    Verifies that required dependencies (PostgreSQL database) are operational.
    Fails with HTTP 503 if the database is unreachable, removing pod from traffic rotation.
    """
    db_status = "UNKNOWN"
    try:
        from db.connection import SessionLocal
        with SessionLocal() as db_session:
            db_session.execute(text("SELECT 1;"))
            db_status = "CONNECTED"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: database unavailable ({str(e)})"
        )

    return {
        "status": "ready",
        "database": db_status,
        "service": "Rahbar API Gateway",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check():
    """Returns comprehensive system health status and telemetry."""
    active_rules = rules_engine.get_active_rules()
    chain_status = audit_log.verify_chain(from_db=False)

    return {
        "status": "healthy",
        "service": "Rahbar API Gateway",
        "version": "1.0.0",
        "boot_time": BOOT_TIME.isoformat(),
        "active_rule_version": active_rules.version,
        "audit_chain_valid": chain_status.is_valid,
        "total_audit_records": chain_status.total_records,
        "audit_head_hash": chain_status.head_hash,
        "dpi_rails_status": {
            "mock_nadra": "OPERATIONAL",
            "mock_raast": "OPERATIONAL",
            "mock_complaints": "OPERATIONAL"
        }
    }
