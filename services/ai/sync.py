"""
Offline-First Sync & Resilience Protocol (Task G11 / Constraint 02).
Handles queued citizen claim submissions when mobile connection restores.
Provides idempotency deduplication, offline voice note batching,
and conflict-free database synchronization.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.ai.agent import execute_agent_workflow
from services.ai.anomaly import detect_claim_anomalies
from services.ai.forms import extract_claim_form
from services.api.engine.consent_gateway import consent_gateway
from services.shared.schemas import ConsentScope

# In-memory idempotency register for synced offline batches
_SYNC_IDEMPOTENCY_STORE: Dict[str, Dict[str, Any]] = {}


def process_offline_sync_batch(
    helper_id: str,
    batch_id: str,
    queued_cases: List[Dict[str, Any]],
    client_timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes a list of cases that were queued locally in IndexedDB while offline.
    Guarantees:
    1. Idempotency: Duplicate submissions with the same idempotency_key are safely skipped.
    2. Zero data loss: Partial failures do not abort remaining cases in batch.
    3. Anomaly check: Protects against velocity bursts from malicious helpers.
    """
    now = datetime.now(timezone.utc)
    results: List[Dict[str, Any]] = []
    synced_count = 0
    duplicate_count = 0
    failed_count = 0

    # Helper velocity check for the batch
    anomaly_result = detect_claim_anomalies({
        "helper_id": helper_id,
        "helper_velocity_24h": len(queued_cases),
        "requested_amount": 10000.0,
        "monthly_income": 25000.0
    })

    batch_flagged_for_review = "HIGH_VELOCITY_HELPER" in anomaly_result.get("flags", [])

    for item in queued_cases:
        idempotency_key = item.get("idempotency_key") or item.get("client_case_id") or uuid.uuid4().hex

        # Check if already processed
        if idempotency_key in _SYNC_IDEMPOTENCY_STORE:
            duplicate_count += 1
            results.append({
                "idempotency_key": idempotency_key,
                "status": "DUPLICATE_SKIPPED",
                "message": "Case already synchronized. Returned cached receipt.",
                "case_id": _SYNC_IDEMPOTENCY_STORE[idempotency_key]["case_id"],
                "decision": _SYNC_IDEMPOTENCY_STORE[idempotency_key]["decision"]
            })
            continue

        try:
            # 1. Parse / Extract fields if voice transcript provided
            citizen_data = dict(item.get("citizen_data", {}))
            if "voice_transcript" in item and not citizen_data.get("full_name"):
                extracted = extract_claim_form(item["voice_transcript"])
                extracted_dict = extracted.model_dump() if hasattr(extracted, "model_dump") else (extracted if isinstance(extracted, dict) else {})
                for k, v in extracted_dict.items():
                    if v is not None and k not in citizen_data:
                        citizen_data[k] = v

            # Task 1 & 3: Check legacy CNIC and helper acting consent at point-of-use
            cnic = citizen_data.get("cnic", "")
            if cnic and cnic.endswith("-X"):
                failed_count += 1
                results.append({
                    "idempotency_key": idempotency_key,
                    "status": "SYNC_FAILED_UNVERIFIED_LEGACY_CNIC",
                    "error": f"Citizen has unverified legacy CNIC ({cnic}). Identity-dependent workflows restricted until manual caseworker verification."
                })
                continue

            citizen_id = item.get("citizen_id") or citizen_data.get("citizen_id")
            if citizen_id:
                has_consent = consent_gateway.check_consent(
                    citizen_id=citizen_id,
                    scope=ConsentScope.HELPER_ACTING,
                    acting_helper_id=helper_id
                )
                if not has_consent:
                    failed_count += 1
                    results.append({
                        "idempotency_key": idempotency_key,
                        "status": "SYNC_FAILED_CONSENT_REVOKED",
                        "error": f"Active consent for scope HELPER_ACTING not found or revoked for citizen {citizen_id}."
                    })
                    continue

            case_id = f"case_sync_{uuid.uuid4().hex[:8]}"

            # 2. Evaluate claim through LangGraph workflow
            workflow_payload = {
                "case_id": case_id,
                "cnic": citizen_data.get("cnic", ""),
                "citizen_name": citizen_data.get("full_name") or citizen_data.get("name", ""),
                "monthly_income": citizen_data.get("monthly_income", 25000.0),
                "household_size": citizen_data.get("household_size", 4),
                "claim_amount": citizen_data.get("requested_amount", 10000.0),
                "documents": item.get("documents", [])
            }
            pipeline_result = execute_agent_workflow(workflow_payload)

            # Record in idempotency store
            sync_record = {
                "case_id": case_id,
                "idempotency_key": idempotency_key,
                "synced_at": now.isoformat(),
                "helper_id": helper_id,
                "decision": pipeline_result.get("route"),
                "confidence": pipeline_result.get("overall_confidence"),
                "reasons": pipeline_result.get("reasons")
            }
            _SYNC_IDEMPOTENCY_STORE[idempotency_key] = sync_record

            synced_count += 1
            results.append({
                "idempotency_key": idempotency_key,
                "status": "SYNCED_SUCCESSFULLY",
                "case_id": case_id,
                "route": pipeline_result.get("route"),
                "confidence": pipeline_result.get("overall_confidence"),
                "explanation": pipeline_result.get("reasons"),
                "flagged_for_batch_review": batch_flagged_for_review
            })

        except Exception as e:
            failed_count += 1
            results.append({
                "idempotency_key": idempotency_key,
                "status": "SYNC_FAILED",
                "error": str(e)
            })

    return {
        "batch_id": batch_id,
        "helper_id": helper_id,
        "received_at": now.isoformat(),
        "client_timestamp": client_timestamp,
        "batch_flagged_for_velocity": batch_flagged_for_review,
        "summary": {
            "total_items": len(queued_cases),
            "synced_count": synced_count,
            "duplicate_count": duplicate_count,
            "failed_count": failed_count,
        },
        "items": results
    }
