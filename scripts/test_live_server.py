"""Quick live integration test verifying local running server."""
import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_live_server():
    # 1. Health
    r_health = httpx.get(f"{BASE_URL}/api/v1/health")
    print(f"[+] Health: {r_health.status_code} -> {r_health.json()['status']}")
    assert r_health.status_code == 200

    # 2. Web App
    r_app = httpx.get(f"{BASE_URL}/app")
    print(f"[+] Web Dashboard (/app): {r_app.status_code} ({len(r_app.text)} bytes)")
    assert r_app.status_code == 200

    # 3. LangGraph ReAct Agent
    payload = {
        "case_id": "live_test_case_001",
        "cnic": "42101-1234567-1",
        "citizen_name": "Parveen Bibi",
        "monthly_income": 25000.0,
        "household_size": 4,
        "claim_amount": 12000.0,
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 1500.0, "tamper_score": 0.01},
            {"doc_type": "utility_bill", "blur_score": 1600.0, "tamper_score": 0.01}
        ]
    }
    r_agent = httpx.post(f"{BASE_URL}/api/v1/ai/agent/run", json=payload)
    print(f"[+] LangGraph Agent Status: {r_agent.status_code}")
    assert r_agent.status_code == 200
    res = r_agent.json()
    print(f"    - Route:            {res.get('route')}")
    print(f"    - Confidence:       {res.get('overall_confidence')*100:.1f}%")
    print(f"    - Disbursed:        {res.get('disbursed')}")
    print(f"    - Raast Reference:  {res.get('disbursement_ref')}")
    print(f"    - Thought Chain:    {len(res.get('thought_chain', []))} steps")
    for s in res.get("thought_chain", []):
        print(f"       * Step {s.get('step')} [{s.get('phase')}]: {s.get('thought')}")

    # 4. Voice TTS
    r_tts = httpx.post(f"{BASE_URL}/api/v1/ai/voice/tts", json={"text": "آپ کی امدادی رقم منظور ہو گئی ہے۔", "language": "ur"})
    print(f"[+] Neural Edge-TTS Stream: {r_tts.status_code} ({len(r_tts.content)} bytes of MP3 audio)")
    assert r_tts.status_code == 200

    print("\n[SUCCESS] ALL LIVE LOCAL ENDPOINTS ARE ACTIVELY RUNNING AND VERIFIED!")

if __name__ == "__main__":
    test_live_server()
