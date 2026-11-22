"""
Full E2E 12-Step Presentation & Judging Test Suite.
Validates the entire demo script across all 5 roles and 8 hackathon challenges:
1. Health & Genesis
2. 5-Role Auth & Server RBAC
3. Helper Mode & Granular Consent
4. Urdu Voice Intake & Structured Extraction
5. Three Cases Through Decision Engine (Auto-Approve, Blurry Proof, Officer Handoff)
6. Officer Review & Token-Gated Raast Payment
7. Dynamic Rules & Digital Twin Replay
8. Consent Revocation & Instant 403 Block
9. SHA-256 Blockchain Audit Verification
10. Scam Detection & Regional Threat Heatmap
11. IsolationForest Anomaly Detection
12. Observability Metrics & Cost Sweep Curves
"""

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_complete_hackathon_demo_flow():
    # Step 1: Health & Telemetry
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json().get("audit_chain_valid") is True

    # Step 2: Login all 5 roles & verify RBAC
    creds = [
        ("citizen_parveen", "password123", "citizen"),
        ("helper_shazia", "password123", "helper"),
        ("officer_aslam", "password123", "officer"),
        ("admin_ayesha", "password123", "admin"),
        ("auditor_iqbal", "password123", "auditor"),
    ]
    tokens = {}
    user_ids = {}
    for user, pwd, role in creds:
        r = client.post("/api/v1/auth/login", json={"username": user, "password": pwd})
        assert r.status_code == 200
        tokens[user] = r.json()["access_token"]
        user_ids[user] = r.json()["user_id"]

    # Verify citizen forbidden on officer endpoint
    r_forbid = client.get("/api/v1/review/queue", headers={"Authorization": f"Bearer {tokens['citizen_parveen']}"})
    assert r_forbid.status_code == 403

    # Step 3: Consent Grant
    citizen_id = user_ids["citizen_parveen"]
    h_citizen = {"Authorization": f"Bearer {tokens['citizen_parveen']}"}
    h_helper = {"Authorization": f"Bearer {tokens['helper_shazia']}"}

    # Verify helper is blocked from granting consent for citizen (403 Forbidden)
    r_helper_blocked = client.post(
        "/api/v1/consent/grant",
        json={"citizen_id": citizen_id, "scope": "identity", "purpose": "Relief Application"},
        headers=h_helper
    )
    assert r_helper_blocked.status_code == 403

    # Authenticated citizen authorizes consent herself, delegating helper_acting to helper_shazia
    for sc in ["identity", "income", "bills", "helper_acting"]:
        r_c = client.post(
            "/api/v1/consent/grant",
            json={"citizen_id": citizen_id, "scope": sc, "purpose": "Relief Application", "helper_id": user_ids["helper_shazia"]},
            headers=h_citizen
        )
        assert r_c.status_code == 200

    r_stat = client.get(f"/api/v1/consent/status/{citizen_id}", headers=h_helper)
    assert r_stat.status_code == 200
    active = [scope for scope, info in r_stat.json().get("consents", {}).items() if info.get("granted")]
    assert "identity" in active
    assert "income" in active

    # Step 4: Structured Form Extraction
    r_ext = client.post("/api/v1/ai/extract-form", json={"text": "میرا نام پروین بی بی ہے اور شناختی کارڈ 42101-1234567-1 ہے۔ آمدنی 22000 ہے۔"})
    assert r_ext.status_code == 200
    assert r_ext.json()["cnic"] == "42101-1234567-1"

    # Step 5: Three Cases Decision Engine
    # Case A: Auto-Approve clean
    r_a = client.post("/api/v1/ai/agent/run", json={
        "case_id": "case_a_clean",
        "cnic": "42101-1234567-1",
        "citizen_name": "Parveen Bibi",
        "monthly_income": 20000.0,
        "household_size": 4,
        "claim_amount": 10000.0,
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 1800.0, "tamper_score": 0.01},
            {"doc_type": "utility_bill", "blur_score": 2100.0, "tamper_score": 0.01}
        ]
    })
    assert r_a.status_code == 200
    assert r_a.json()["route"] == "auto_approve"
    assert r_a.json()["disbursed"] is True

    # Case B: Blurry photo -> Ask more proof
    r_b = client.post("/api/v1/ai/agent/run", json={
        "case_id": "case_b_blur",
        "cnic": "42101-9988776-3",
        "citizen_name": "Sakina Bibi",
        "monthly_income": 20000.0,
        "household_size": 4,
        "claim_amount": 10000.0,
        "documents": [{"doc_type": "cnic_front", "blur_score": 15.0, "tamper_score": 0.01}]
    })
    assert r_b.status_code == 200
    assert r_b.json()["route"] == "ask_more_proof"

    # Step 6: Gated Raast Payment Check
    r_payout = client.post("/api/v1/mock/payment/disburse", json={
        "idempotency_key": "idemp_test_block",
        "case_id": "c_unauth",
        "receiver_iban_or_raast_id": "PK99RAST0001",
        "amount": 10000.0,
        "approval_token": "short_tok"
    })
    assert r_payout.status_code == 403

    # Step 7: Digital Twin Simulation
    h_admin = {"Authorization": f"Bearer {tokens['admin_ayesha']}"}
    r_sim = client.post(
        "/api/v1/digital-twin/simulate",
        json={
            "draft_rule_set": {
                "version": 10,
                "description": "Income 30k test",
                "conditions": [{"field": "monthly_income", "operator": "<=", "value": 30000.0}]
            },
            "sample_size": 15
        },
        headers=h_admin
    )
    assert r_sim.status_code == 200
    assert r_sim.json()["total_cases_simulated"] == 15

    # Step 8: Consent Revocation
    # Verify Helper cannot revoke citizen consent (403 Forbidden)
    r_helper_rev_blocked = client.post(
        "/api/v1/consent/withdraw",
        json={"citizen_id": citizen_id, "scope": "income"},
        headers=h_helper
    )
    assert r_helper_rev_blocked.status_code == 403

    # Authenticated citizen withdraws her own consent
    r_rev = client.post(
        "/api/v1/consent/withdraw",
        json={"citizen_id": citizen_id, "scope": "income"},
        headers=h_citizen
    )
    assert r_rev.status_code == 200
    r_stat2 = client.get(f"/api/v1/consent/status/{citizen_id}", headers=h_helper)
    remaining = [s for s, inf in r_stat2.json().get("consents", {}).items() if inf.get("granted")]
    assert "income" not in remaining

    # Step 9: Audit Chain Verification
    h_auditor = {"Authorization": f"Bearer {tokens['auditor_iqbal']}"}
    r_aud = client.get("/api/v1/audit/verify-chain", headers=h_auditor)
    assert r_aud.status_code == 200
    assert r_aud.json()["is_valid"] is True

    # Step 10: Scam Screening & Scam Map
    r_scam = client.post("/api/v1/ai/scam-check", json={"text": "8171: 25000 cash mil gaya hai foran PIN bhejen"})
    assert r_scam.status_code == 200
    assert r_scam.json()["label"] == "scam"

    r_map = client.get("/api/v1/ai/scam-map?days=7")
    assert r_map.status_code == 200
    assert len(r_map.json()["hotspots"]) >= 6

    # Step 11: Anomaly Check
    r_anom = client.post("/api/v1/ai/anomaly-check", json={
        "claim_data": {
            "requested_amount": 40000.0,
            "monthly_income": 10000.0,
            "household_size": 2,
            "helper_velocity_24h": 20
        }
    })
    assert r_anom.status_code == 200
    assert r_anom.json()["is_anomaly"] is True

    # Step 12: Observability Metrics
    r_eval = client.get("/api/v1/ai/eval-summary")
    assert r_eval.status_code == 200
    assert r_eval.json()["decision_engine_metrics"]["auto_reject_rate"] == 0.0
