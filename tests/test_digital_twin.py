"""
Tests for Digital Twin Simulation Engine.
Implements Creative Bonus Feature:
Replays past/synthetic cases under a draft rule version to project approval rate changes
and fiscal impact before publishing.
"""
from fastapi.testclient import TestClient


def test_digital_twin_simulate_impact(client: TestClient, admin_headers: dict):
    draft_payload = {
        "draft_rule_set": {
            "version": 2,
            "name": "Higher Relief Threshold v2.0",
            "max_monthly_income": 45000.0,
            "min_household_size": 1,
            "max_auto_approve_amount": 18000.0,
            "requires_valid_cnic": True,
            "requires_utility_bill": True,
            "max_wrong_prob_auto_approve": 0.05,
            "max_wrong_prob_ask_proof": 0.30
        },
        "sample_size": 25
    }

    resp = client.post("/api/v1/digital-twin/simulate", json=draft_payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cases_simulated"] == 25
    assert "previous_approval_rate" in data
    assert "projected_approval_rate" in data
    assert "approval_rate_delta" in data
    assert "impact_summary" in data
    assert isinstance(data["affected_case_ids"], list)
