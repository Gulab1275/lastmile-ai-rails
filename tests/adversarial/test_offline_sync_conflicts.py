"""
Adversarial Test Suite K: Offline Sync, Batch Deduplication & Partition Resilience.
Tests J01 - J06: Evaluates idempotency deduplication across batch IDs,
partial batch fault tolerance, malformed payload isolation, and conflict resolution.
"""
import uuid

from services.ai.sync import process_offline_sync_batch
from services.api.engine.consent_gateway import consent_gateway
from services.shared.schemas import ConsentScope, RoleEnum


def _setup_sync_citizen(citizen_id: str = "cit_sync_khadija", helper_id: str = "helper_shazia"):
    """Ensures verified citizen registration and active HELPER_ACTING consent prior to offline sync."""
    consent_gateway.grant_consent(
        citizen_id=citizen_id,
        scope=ConsentScope.HELPER_ACTING,
        helper_id=helper_id,
        actor_id=citizen_id,
        actor_role=RoleEnum.CITIZEN
    )


def _sample_queued_item(idemp_key=None, income=20000.0, name="Khadija Bibi", citizen_id="cit_sync_khadija"):
    _setup_sync_citizen(citizen_id=citizen_id, helper_id="helper_shazia")
    return {
        "idempotency_key": idemp_key or f"off_idemp_{uuid.uuid4().hex[:8]}",
        "citizen_id": citizen_id,
        "citizen_data": {
            "full_name": name,
            "cnic": "42101-5544332-1",
            "monthly_income": income,
            "household_size": 4,
            "requested_amount": 12000.0
        },
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 1500.0, "tamper_score": 0.01}
        ]
    }


def test_j01_submit_same_batch_twice_fully_deduplicated():
    """J01: Submitting the identical batch twice results in 100% duplicate skips on second attempt."""
    shared_key = f"off_batch_key_{uuid.uuid4().hex[:8]}"
    item = _sample_queued_item(idemp_key=shared_key)
    batch_payload = [item]

    res1 = process_offline_sync_batch("helper_shazia", "batch_001", batch_payload)
    assert res1["summary"]["synced_count"] == 1
    assert res1["summary"]["duplicate_count"] == 0

    res2 = process_offline_sync_batch("helper_shazia", "batch_002", batch_payload)
    assert res2["summary"]["synced_count"] == 0
    assert res2["summary"]["duplicate_count"] == 1
    assert res2["items"][0]["status"] == "DUPLICATE_SKIPPED"


def test_j02_same_claim_different_batch_ids_deduplicated():
    """J02: Same underlying claim submitted across two different batch IDs is recognized and deduplicated."""
    shared_key = f"off_cross_key_{uuid.uuid4().hex[:8]}"
    item1 = _sample_queued_item(idemp_key=shared_key, income=18000.0)
    item2 = _sample_queued_item(idemp_key=shared_key, income=18000.0)

    res1 = process_offline_sync_batch("helper_shazia", "batch_alpha", [item1])
    res2 = process_offline_sync_batch("helper_shazia", "batch_beta", [item2])

    assert res1["summary"]["synced_count"] == 1
    assert res2["summary"]["synced_count"] == 0
    assert res2["summary"]["duplicate_count"] == 1


def test_j03_offline_and_online_data_preserves_idempotency_receipt():
    """J03: Cached decision receipt returned on duplicate submission preserves original case ID."""
    shared_key = f"off_receipt_key_{uuid.uuid4().hex[:8]}"
    item = _sample_queued_item(idemp_key=shared_key)

    res1 = process_offline_sync_batch("helper_shazia", "batch_rec_1", [item])
    orig_case_id = res1["items"][0]["case_id"]

    res2 = process_offline_sync_batch("helper_shazia", "batch_rec_2", [item])
    cached_case_id = res2["items"][0]["case_id"]

    assert orig_case_id == cached_case_id


def test_j04_malformed_records_mixed_with_valid_do_not_abort_batch():
    """J06: Malformed records mixed with valid records: valid are processed, malformed captured in failed_count."""
    valid_item = _sample_queued_item(name="Zahida Parveen", citizen_id="cit_sync_zahida")
    # Missing citizen_data or invalid type
    malformed_item = {
        "idempotency_key": f"off_mal_{uuid.uuid4().hex[:8]}",
        "citizen_data": "NOT_A_DICT",  # Invalid type triggers exception in item processing
        "documents": []
    }

    res = process_offline_sync_batch("helper_shazia", "batch_mixed", [valid_item, malformed_item])

    assert res["summary"]["total_items"] == 2
    assert res["summary"]["synced_count"] == 1
    assert res["summary"]["failed_count"] == 1
    assert any(i["status"] == "SYNC_FAILED" for i in res["items"])


def test_j05_high_velocity_batch_flagged_for_review():
    """J05: Batch containing abnormally high number of cases triggers velocity anomaly flag."""
    large_batch = [_sample_queued_item() for _ in range(25)]
    res = process_offline_sync_batch("helper_shazia", "batch_large_25", large_batch)

    # 25 submissions in one batch triggers high velocity check (> 15)
    assert res["batch_flagged_for_velocity"] is True
