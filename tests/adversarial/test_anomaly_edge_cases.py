"""
Adversarial Test Suite L: Anomaly Detection Statistical Outliers & Boundary Cases.
Tests K01 - K06: Evaluates Isolation Forest feature extraction, repeat CNIC bursts,
velocity thresholds, and separation of statistical anomaly from confirmed fraud.
"""
from services.ai.anomaly import detect_claim_anomalies, extract_claim_features


def test_k01_normal_helper_activity_not_flagged_as_fraud():
    """K01: One helper submits 10 claims over 7 days (velocity = 2). Normal behavior is not flagged."""
    normal_claim = {
        "requested_amount": 10000.0,
        "monthly_income": 25000.0,
        "household_size": 4,
        "helper_velocity_24h": 2
    }
    res = detect_claim_anomalies(normal_claim)

    assert res["is_anomaly"] is False
    assert res["anomaly_score"] < 0.40
    assert "HIGH_VELOCITY_HELPER" not in res["flags"]


def test_k02_repeat_cnic_burst_detection():
    """K03: Same CNIC submitted repeatedly across 15 claims in 24 hours."""
    historical = [
        {"case_id": f"cas_hist_{i}", "cnic": "42101-1234567-1", "phone": "03001234567"}
        for i in range(14)
    ]
    incoming_claim = {
        "case_id": "cas_new_15",
        "cnic": "42101-1234567-1",
        "phone": "03001234567",
        "requested_amount": 12000.0,
        "monthly_income": 20000.0
    }
    res = detect_claim_anomalies(incoming_claim, historical_claims=historical)

    assert res["is_anomaly"] is True
    assert "REPEAT_CNIC_CLAIM" in res["flags"]
    assert "REPEAT_PHONE_BURST" in res["flags"]


def test_k03_income_to_claim_ratio_divergence():
    """K04: Requested amount substantially exceeds monthly income (ratio > 1.2)."""
    divergent_claim = {
        "requested_amount": 25000.0,
        "monthly_income": 12000.0,  # Ratio 25k/12k = 2.08 > 1.2 threshold
        "household_size": 4
    }
    res = detect_claim_anomalies(divergent_claim)

    assert res["is_anomaly"] is True
    assert "SUSPICIOUS_INCOME_TO_CLAIM_RATIO" in res["flags"]


def test_k04_helper_velocity_spike_flagged():
    """K05: Helper suddenly submits 40 claims within 24 hours."""
    high_velocity_claim = {
        "requested_amount": 10000.0,
        "monthly_income": 25000.0,
        "household_size": 4,
        "helper_velocity_24h": 40  # Velocity spike > 15
    }
    res = detect_claim_anomalies(high_velocity_claim)

    assert res["is_anomaly"] is True
    assert "HIGH_VELOCITY_HELPER" in res["flags"]


def test_k05_extreme_numerical_values_handled_gracefully():
    """K06: Extreme numerical values (e.g. 100 million) do not crash feature extraction."""
    extreme_claim = {
        "requested_amount": 100000000.0,
        "monthly_income": 0.0,
        "household_size": 0,
        "helper_velocity_24h": 9999
    }
    features = extract_claim_features(extreme_claim)

    assert len(features) == 7
    # Feature 3 (household_size) should have min-clamp 1 to prevent division by zero
    assert features[3] >= 1


def test_k06_bilingual_explanations_provided_for_every_anomaly():
    """K06: Every flagged anomaly includes both English and Urdu explanations for transparency."""
    claim = {
        "requested_amount": 25000.0,
        "monthly_income": 10000.0,
        "helper_velocity_24h": 30
    }
    res = detect_claim_anomalies(claim)

    assert len(res["reasons_en"]) > 0
    assert len(res["reasons_ur"]) > 0
    assert len(res["reasons_en"]) == len(res["reasons_ur"])
