"""
System Health & Telemetry Endpoint.
"""
from datetime import datetime

from fastapi import APIRouter

from services.api.engine.audit_log import audit_log
from services.api.engine.rules_engine import rules_engine

router = APIRouter(tags=["Health & Status"])

BOOT_TIME = datetime.utcnow()


@router.get("/health")
async def health_check():
    """Returns comprehensive system health status and telemetry."""
    active_rules = rules_engine.get_active_rules()
    chain_status = audit_log.verify_chain()

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
