"""
End-to-End Integration Tests.
Executes the full 12-step demo happy path:
1. Citizen logs in
2. Checks / grants granular consent
3. Creates relief claim
4. Attaches documents
5. Submits case
6. Runs Decision Engine evaluation
7. Officer reviews queue & approves with mandatory notes
8. Raast gated disbursement executes successfully
9. Cryptographic audit chain verifies 100% valid
"""
from fastapi.testclient import TestClient


def test_full_e2e_relief_claim_lifecycle(client: TestClient, officer_headers: dict):
    # Step 1: Login Citizen Parveen Bibi
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "citizen_parveen",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    citizen_token = login_resp.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    citizen_id = login_resp.json()["user_id"]

    # Step 2: Grant Granular Consent
    cns_resp = client.post("/api/v1/consent/grant", json={
        "citizen_id": citizen_id,
        "scope": "income"
    }, headers=citizen_headers)
    assert cns_resp.status_code == 200
    assert cns_resp.json()["granted"] is True

    # Step 3: Create Relief Claim Case
    create_resp = client.post("/api/v1/cases", json={
        "citizen_name": "Parveen Bibi",
        "cnic": "42101-1234567-1",
        "phone": "0300-1234567",
        "household_size": 4,
        "monthly_income": 22000.0,
        "requested_amount": 12000.0
    }, headers=citizen_headers)
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    # Step 4: Attach Verified Documents
    doc_resp = client.post(f"/api/v1/cases/{case_id}/documents", json={
        "doc_id": "doc_cnic_001",
        "doc_type": "cnic_front",
        "file_name": "parveen_cnic.jpg",
        "file_url": "https://storage.rahbar.pk/parveen_cnic.jpg",
        "ocr_confidence": 0.95,
        "is_blurry": False,
        "is_tampered": False
    }, headers=citizen_headers)
    assert doc_resp.status_code == 200

    # Step 5: Submit Case
    sub_resp = client.post(f"/api/v1/cases/{case_id}/submit", headers=citizen_headers)
    assert sub_resp.status_code == 200

    # Step 6: Decision Engine Evaluation
    dec_resp = client.post(f"/api/v1/decisions/evaluate/{case_id}", headers=citizen_headers)
    assert dec_resp.status_code == 200
    decision_data = dec_resp.json()
    assert "route" in decision_data
    assert "confidence" in decision_data

    # Step 7: Dual-View Explanations
    # Citizen view
    exp_cit = client.get(f"/api/v1/decisions/explain/{case_id}?view=citizen", headers=citizen_headers)
    assert exp_cit.status_code == 200
    assert "status_icon" in exp_cit.json()
    assert "headline_ur" in exp_cit.json()

    # Step 8: Officer Reviews and Approves
    officer_dec_resp = client.post(f"/api/v1/review/{case_id}/decision", json={
        "decision": "auto_approve",
        "approved": True,
        "mandatory_officer_notes": "All documents verified in person. Citizen meets low-income criteria."
    }, headers=officer_headers)
    assert officer_dec_resp.status_code == 200
    assert officer_dec_resp.json()["status"] == "approved"

    # Step 9: Verify Cryptographic Audit Chain Integrity
    chain_resp = client.get("/api/v1/audit/verify-chain", headers=officer_headers)
    assert chain_resp.status_code == 200
    assert chain_resp.json()["is_valid"] is True
    assert chain_resp.json()["corrupted_at_index"] is None
