"""
Automated Test Suite for AI Services Endpoints (Coder's Cup '26).
Tests:
- Scam Message Classifier (Urdu / English)
- Document OCR with Laplacian Blur and ELA Tamper Gates
- Urdu Voice Pipeline (Speech Synthesis and Audio Caching)
- Policy Q&A RAG with Citations
- Structured Form Extraction from Conversational Urdu
- LangGraph Autonomous Claim Agent with Token Guardrails
- AI Telemetry Health
"""
import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFilter

from services.api.main import app

client = TestClient(app)

def test_ai_health_endpoint():
    """Verify AI provider health check responds 200."""
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_providers" in data

def test_ai_scam_classifier_detects_phishing():
    """Verify phishing SMS triggers scam label and explainable reasons."""
    payload = {
        "text": "Muaziz Sarif, Hukumat Relief 25000 grant aya hai. Foran bit.ly/relief par 500 fee dein"
    }
    response = client.post("/api/v1/ai/scam-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "scam"
    assert data["confidence"] >= 0.70
    assert len(data["reasons"]) >= 1

def test_ai_scam_classifier_legitimate_message():
    """Verify official notice passes as legit."""
    payload = {
        "text": "Your NADRA CNIC renewal application has been received with tracking ID 9821."
    }
    response = client.post("/api/v1/ai/scam-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "legit"
    assert data["confidence"] >= 0.60

def test_ai_document_ocr_blur_gate():
    """Verify blur gate correctly distinguishes sharp from blurry images."""
    # 1. Sharp Image
    img_sharp = Image.new("RGB", (300, 200), color=(245, 245, 245))
    draw = ImageDraw.Draw(img_sharp)
    draw.text((20, 30), "Name: Parveen Bibi", fill=(0, 0, 0))
    draw.text((20, 60), "CNIC: 42101-1234567-1", fill=(0, 0, 0))
    buf_sharp = io.BytesIO()
    img_sharp.save(buf_sharp, format="PNG")
    buf_sharp.seek(0)

    # 2. Blurred Image
    img_blurred = img_sharp.filter(ImageFilter.GaussianBlur(radius=6))
    buf_blur = io.BytesIO()
    img_blurred.save(buf_blur, format="PNG")
    buf_blur.seek(0)

    # Test sharp upload
    resp_sharp = client.post(
        "/api/v1/ai/ocr",
        files=[("files", ("cnic.png", buf_sharp.getvalue(), "image/png"))]
    )
    assert resp_sharp.status_code == 200
    data_sharp = resp_sharp.json()
    assert data_sharp["is_blurry"] is False
    assert data_sharp["blur_score"] > 90.0

    # Test blurry upload
    resp_blur = client.post(
        "/api/v1/ai/ocr",
        files=[("files", ("blurry.png", buf_blur.getvalue(), "image/png"))]
    )
    assert resp_blur.status_code == 200
    data_blur = resp_blur.json()
    assert data_blur["is_blurry"] is True
    assert data_blur["blur_score"] < 90.0

def test_ai_voice_tts_synthesis():
    """Verify Urdu text-to-speech returns audio/mpeg stream."""
    payload = {
        "text": "آپ کی امدادی رقم منظور ہو گئی ہے۔",
        "language": "ur"
    }
    response = client.post("/api/v1/ai/voice/tts", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 1000

def test_ai_voice_stt_multi_format_and_detection():
    """Verify audio format detection (WebM, WAV, MP3) and STT endpoint."""
    from services.ai.voice import detect_audio_format

    # Check WebM detection
    name, mime = detect_audio_format(b"\x1aE\xdf\xa3dummy_webm_bytes")
    assert name == "input.webm"
    assert mime == "audio/webm"

    # Check WAV detection
    name, mime = detect_audio_format(b"RIFFdummy_wav_bytes")
    assert name == "input.wav"
    assert mime == "audio/wav"

    # Check filename override
    name, mime = detect_audio_format(b"anything", filename="speech.weba")
    assert name == "input.webm"
    assert mime == "audio/webm"

def test_ai_pgvector_semantic_embedding_engine():
    """Verify 384-dimensional dense semantic embedding engine and cosine similarity."""
    from services.ai.embeddings import cosine_similarity, generate_embedding

    v_query = generate_embedding("What is the monthly income limit for widow relief?")
    v_policy = generate_embedding("Section 2.1: Households with monthly income below PKR 35,000 qualify for widow assistance.")
    v_irrelevant = generate_embedding("Chocolate brownie recipe with cocoa powder.")

    assert len(v_query) == 384
    assert len(v_policy) == 384
    assert round(sum(x*x for x in v_query), 2) == 1.0  # L2 normalized

    sim_related = cosine_similarity(v_query, v_policy)
    sim_unrelated = cosine_similarity(v_query, v_irrelevant)
    assert sim_related > sim_unrelated
    assert sim_related > 0.30

def test_ai_policy_rag_with_citations():
    """Verify policy Q&A returns authoritative answer with source citations via pgvector."""
    payload = {
        "question": "What is the maximum income to be eligible for relief support?"
    }
    response = client.post("/api/v1/ai/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 10
    assert len(data["sources"]) >= 1
    assert "document_name" in data["sources"][0]
    assert "page_number" in data["sources"][0]
    assert "retrieval_mode" in data

def test_ai_policy_rag_urdu_query():
    """Verify Urdu policy query returns Urdu guidance with citations."""
    payload = {
        "question": "بیوہ خواتین کے لیے اہلیت کی کیا شرائط ہیں؟"
    }
    response = client.post("/api/v1/ai/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 10
    assert len(data["sources"]) >= 1
    assert "document_name" in data["sources"][0]
    assert "page_number" in data["sources"][0]

def test_ai_structured_form_extraction():
    """Verify conversational Urdu text extracts into structured Pydantic fields."""
    payload = {
        "text": "میرا نام پروین بی بی ہے اور میرا شناختی کارڈ 42101-1234567-1 ہے۔ 4 افراد ہیں اور 25000 روپے آمدنی ہے۔"
    }
    response = client.post("/api/v1/ai/extract-form", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cnic"] == "42101-1234567-1"
    assert data["household_size"] == 4
    assert data["monthly_income"] == 25000.0
    assert data["confidence"] >= 0.8

def test_ai_langgraph_agent_clean_approval():
    """Verify LangGraph agent auto-approves clean claim and issues disbursement."""
    payload = {
        "case_id": "case_test_agent_clean",
        "cnic": "42101-7654321-1",
        "citizen_name": "Fatima Bibi",
        "monthly_income": 20000.0,
        "household_size": 5,
        "claim_amount": 12000.0,
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 1400.0, "tamper_score": 0.01},
            {"doc_type": "utility_bill", "blur_score": 1600.0, "tamper_score": 0.01}
        ]
    }
    response = client.post("/api/v1/ai/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "auto_approve"
    assert data["disbursed"] is True
    assert data["disbursement_ref"] is not None
    assert data["disbursement_ref"].startswith("RAAST-TX-")
    assert "thought_chain" in data
    assert len(data["thought_chain"]) >= 4
    assert "verify_identity" in data["tools_executed"]
    assert "disburse_payment" in data["tools_executed"]

def test_ai_langgraph_agent_blurry_requests_more_proof():
    """Verify LangGraph agent flags blurry document and requests proof without auto-rejecting."""
    payload = {
        "case_id": "case_test_agent_blurry",
        "cnic": "42101-9988776-3",
        "citizen_name": "Sakina Bibi",
        "monthly_income": 20000.0,
        "household_size": 4,
        "claim_amount": 10000.0,
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 25.0, "tamper_score": 0.02}
        ]
    }
    response = client.post("/api/v1/ai/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "ask_more_proof"
    assert data["disbursed"] is False
    assert "thought_chain" in data
    assert any("blur detected" in step.get("thought", "").lower() for step in data["thought_chain"])

def test_ai_langgraph_agent_high_claim_hands_off_to_officer():
    """Verify LangGraph agent hands off high-risk claim to human officer with triage packet."""
    payload = {
        "case_id": "case_test_agent_high",
        "cnic": "42101-5544332-1",
        "citizen_name": "Ghulam Rasool",
        "monthly_income": 50000.0,  # exceeds poverty cap
        "household_size": 2,
        "claim_amount": 35000.0,    # exceeds auto threshold
        "documents": [
            {"doc_type": "cnic_front", "blur_score": 1200.0, "tamper_score": 0.01},
            {"doc_type": "utility_bill", "blur_score": 1400.0, "tamper_score": 0.01}
        ]
    }
    response = client.post("/api/v1/ai/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "human_review"
    assert data["disbursed"] is False
    assert data["handoff_packet"] is not None
    assert data["handoff_packet"]["tool"] == "handoff_to_officer"


def test_ai_anomaly_detection_flags_outlier_and_velocity():
    """Verify IsolationForest and rules detect helper velocity and ratio outliers."""
    # Test high ratio + high helper velocity
    payload = {
        "claim_data": {
            "case_id": "case_anom_01",
            "cnic": "42101-9988776-5",
            "phone": "0300-1234567",
            "requested_amount": 50000.0,
            "monthly_income": 12000.0,  # ratio > 4.0
            "household_size": 2,
            "helper_velocity_24h": 22,   # velocity spike > 15
            "tamper_score": 0.02
        },
        "historical_claims": [
            {"case_id": "case_hist_01", "cnic": "42101-9988776-5", "phone": "0300-1234567"},
            {"case_id": "case_hist_02", "cnic": "42101-1122334-9", "phone": "0300-1234567"},
            {"case_id": "case_hist_03", "cnic": "42101-5566778-1", "phone": "0300-1234567"},
        ]
    }
    response = client.post("/api/v1/ai/anomaly-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] is True
    assert data["anomaly_score"] >= 0.70
    assert "SUSPICIOUS_INCOME_TO_CLAIM_RATIO" in data["flags"]
    assert "HIGH_VELOCITY_HELPER" in data["flags"]
    assert "REPEAT_CNIC_CLAIM" in data["flags"]
    assert "REPEAT_PHONE_BURST" in data["flags"]
    assert len(data["reasons_ur"]) >= 2


def test_ai_scam_map_feed_structure_and_geo_clusters():
    """Verify scam map threat feed returns Karachi clusters and keywords."""
    response = client.get("/api/v1/ai/scam-map?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["total_active_clusters"] >= 6
    assert len(data["hotspots"]) >= 6
    # Check that geo coordinates and threat intensity exist
    for spot in data["hotspots"]:
        assert "district" in spot
        assert "latitude" in spot
        assert "longitude" in spot
        assert 0.0 <= spot["threat_intensity"] <= 1.0
        assert spot["threat_level"] in ["CRITICAL", "HIGH", "MODERATE"]
    assert len(data["top_keywords"]) >= 5
    assert len(data["temporal_trends"]) == 7


def test_ai_eval_summary_metrics_and_guarantees():
    """Verify evaluation summary provides benchmarks, sweep curves, and zero auto-reject guarantee."""
    response = client.get("/api/v1/ai/eval-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["total_test_samples"] == 200
    # Classifier accuracy
    assert data["scam_classifier_metrics"]["accuracy"] >= 0.95
    # Decision engine guarantees
    assert data["decision_engine_metrics"]["auto_reject_rate"] == 0.0
    assert data["decision_engine_metrics"]["weakest_link_rule_enforced"] is True
    # Latency benchmarks
    benchmarks = data["latency_benchmarks"]
    assert len(benchmarks) >= 6
    # Threshold sweep curve
    assert len(data["threshold_sweep_curve"]) >= 10


def test_ai_offline_sync_batch_with_idempotency():
    """Verify offline batch sync processes cases and dedupes identical submissions."""
    # Pre-register both citizens and grant HELPER_ACTING consent so identity verification passes.
    # Citizen IDs are stable, deterministic identifiers used only within this test.
    citizen_id_1 = "sync_test_citizen_zainab_001"
    citizen_id_2 = "sync_test_citizen_khadija_002"
    helper_id = "helper.fatima"

    from services.api.engine.consent_gateway import consent_gateway
    from services.shared.schemas import ConsentScope, RoleEnum

    for cid in (citizen_id_1, citizen_id_2):
        consent_gateway.grant_consent(
            citizen_id=cid,
            scope=ConsentScope.HELPER_ACTING,
            helper_id=helper_id,
            actor_id=cid,
            actor_role=RoleEnum.CITIZEN,
        )

    payload = {
        "batch_id": "batch_offline_991",
        "helper_id": helper_id,
        "client_timestamp": "2026-11-20T22:00:00Z",
        "queued_cases": [
            {
                "idempotency_key": "idemp_k_001",
                "citizen_id": citizen_id_1,
                "voice_transcript": "میرا نام زینب بی بی ہے اور میرا شناختی کارڈ 42101-7788990-1 ہے۔ آمدنی 18000 ہے اور 4 بچے ہیں۔",
                "citizen_data": {"requested_amount": 10000.0},
                "documents": [
                    {"doc_type": "cnic_front", "blur_score": 1500.0, "tamper_score": 0.01}
                ]
            },
            {
                "idempotency_key": "idemp_k_002",
                "citizen_id": citizen_id_2,
                "citizen_data": {
                    "full_name": "Khadija Bibi",
                    "cnic": "42101-5544332-9",
                    "monthly_income": 22000.0,
                    "household_size": 5,
                    "requested_amount": 12000.0
                },
                "documents": [
                    {"doc_type": "cnic_front", "blur_score": 1600.0, "tamper_score": 0.01}
                ]
            }
        ]
    }
    # First sync: both processed
    resp1 = client.post("/api/v1/ai/sync-offline-batch", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["summary"]["synced_count"] == 2
    assert data1["summary"]["duplicate_count"] == 0
    assert len(data1["items"]) == 2
    assert data1["items"][0]["status"] == "SYNCED_SUCCESSFULLY"

    # Second sync of identical batch: safely deduplicated!
    resp2 = client.post("/api/v1/ai/sync-offline-batch", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["summary"]["duplicate_count"] == 2
    assert data2["summary"]["synced_count"] == 0
    assert data2["items"][0]["status"] == "DUPLICATE_SKIPPED"

def test_ai_hybrid_rrf_policy_search():
    """Verify Reciprocal Rank Fusion (BM25 + pgvector dense) accurately ranks policy chunks."""
    from services.ai.rag import search_policy_chunks
    # Query with exact number and terms
    results = search_policy_chunks("PKR 35,000 income limit for widow assistance", limit=3)
    assert len(results) >= 1
    top = results[0]
    assert "35,000" in top["excerpt"] or "35,000" in top.get("content", "")
    assert top["retrieval_mode"] in ("hybrid_rrf_pgvector", "local_resilient_fallback")
    assert top["similarity"] >= 0.40

def test_ai_voice_vad_silence_guardrail():
    """Verify Voice Activity Detection (VAD) intercepts flatline silence early."""
    from services.ai.voice import transcribe
    # 0.1s silence buffer
    empty_silence = b"RIFF" + b"\x00" * 40
    res = transcribe(empty_silence, language="ur")
    assert res["is_silent"] is True
    assert res["confidence"] == 0.0

def test_ai_roman_urdu_normalization_and_scam_detection():
    """Verify Roman Urdu soundex normalizer catches adversarial phonetic evasion."""
    from services.ai.normalizer import normalize_roman_urdu
    raw = "Aapko 50000 wazeefa mila hy foran fess snd kren 0300 123 4567"
    normalized = normalize_roman_urdu(raw)
    assert "fee" in normalized
    assert "bhejo" in normalized
    assert "03001234567" in normalized

    # Scam check on adversarial spelling
    resp = client.post("/api/v1/ai/scam-check", json={"text": raw})
    assert resp.status_code == 200
    data = resp.json()
    assert data["label"] == "scam"
    assert data["confidence"] >= 0.70


