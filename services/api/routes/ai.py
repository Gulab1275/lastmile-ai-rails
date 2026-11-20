"""
AI Services REST Endpoints for Rahbar API Gateway.
Routes:
- POST /api/v1/ai/scam-check
- POST /api/v1/ai/ocr
- POST /api/v1/ai/voice/stt
- POST /api/v1/ai/voice/tts
- POST /api/v1/ai/ask (RAG)
- POST /api/v1/ai/extract-form
- POST /api/v1/ai/agent/run (LangGraph)
- GET  /api/v1/ai/health
"""
import io
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import StreamingResponse

from services.shared.schemas import (
    ScamCheckRequest, ScamCheckResponse,
    DocumentExtractionResult,
    TranscribeResponse, SynthesizeRequest,
    PolicyAskRequest, PolicyAskResponse,
    AnomalyCheckRequest, AnomalyCheckResponse,
    OfflineSyncBatchRequest
)
from services.ai.scam import classify_message
from services.ai.ocr import extract_documents
from services.ai.voice import transcribe, synthesize
from services.ai.rag import ask_policy
from services.ai.forms import extract_claim_form, ExtractedClaimForm
from services.ai.agent import execute_agent_workflow
from services.ai.router import check_llm_health
from services.ai.anomaly import detect_claim_anomalies
from services.ai.scam_map import generate_scam_map_feed
from services.ai.eval_dashboard import get_evaluation_dashboard_metrics
from services.ai.sync import process_offline_sync_batch

router = APIRouter(prefix="/ai", tags=["AI & Agents"])

@router.post("/scam-check", response_model=ScamCheckResponse)
def check_scam_message(payload: ScamCheckRequest):
    """
    Detects whether an SMS / WhatsApp message is fraudulent, legitimate, or uncertain.
    Provides calibrated confidence and explainable trigger reasons.
    """
    res = classify_message(payload.text)
    return ScamCheckResponse(
        label=res["label"],
        confidence=res["confidence"],
        reasons=res["reasons"]
    )

@router.post("/ocr", response_model=DocumentExtractionResult)
async def analyze_document_ocr(files: List[UploadFile] = File(...)):
    """
    Analyzes uploaded document images (CNIC, utility bills).
    Performs Laplacian blur detection, Error Level Analysis (ELA) tamper check,
    and regex field extraction.
    """
    file_bytes_list = []
    for f in files:
        data = await f.read()
        file_bytes_list.append(data)
    
    res = extract_documents(file_bytes_list)
    return DocumentExtractionResult(
        fields=res["fields"],
        field_confidences=res["field_confidences"],
        blur_score=res["blur_score"],
        is_blurry=res["is_blurry"],
        tamper_score=res["tamper_score"]
    )

@router.post("/voice/stt", response_model=TranscribeResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form("ur")
):
    """
    Transcribes spoken Urdu or English audio into text using Groq Whisper-large-v3.
    """
    audio_data = await file.read()
    res = transcribe(
        audio_data,
        language=language,
        filename=file.filename,
        content_type=file.content_type
    )
    return TranscribeResponse(
        text=res["text"],
        language=res["language"],
        confidence=res["confidence"]
    )

@router.post("/voice/tts")
def text_to_speech(payload: SynthesizeRequest):
    """
    Synthesizes Urdu or English text into natural voice audio (MP3).
    Cached by text hash for fast repeated delivery.
    """
    audio_bytes = synthesize(payload.text, lang=payload.language)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Text-to-speech generation failed")
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )

@router.post("/ask", response_model=PolicyAskResponse)
def ask_policy_question(payload: PolicyAskRequest):
    """
    Answers relief eligibility and policy questions directly from official guidelines.
    Returns plain answer with exact document and page citations.
    """
    res = ask_policy(payload.question)
    return PolicyAskResponse(
        answer=res["answer"],
        sources=res["sources"]
    )

@router.post("/extract-form", response_model=ExtractedClaimForm)
def extract_form_from_text(payload: Dict[str, str]):
    """
    Converts unstructured conversational Urdu or English input into a validated Pydantic claim form.
    """
    text = payload.get("text", "")
    return extract_claim_form(text)

@router.post("/agent/run")
def run_autonomous_agent(payload: Dict[str, Any]):
    """
    Executes the checkpointed LangGraph relief claim workflow.
    Evaluates documents, identity, rules, risk, and executes gated payment if approved.
    """
    res = execute_agent_workflow(payload)
    return {
        "case_id": res["case_id"],
        "route": res["route"],
        "overall_confidence": res["overall_confidence"],
        "reasons": res["reasons"],
        "disbursed": res["disbursed"],
        "disbursement_ref": res["disbursement_ref"],
        "current_step": res["current_step"]
    }

@router.get("/health")
def get_ai_services_health():
    """
    Telemetry on AI providers (Groq, Gemini) latency and availability.
    """
    return {
        "status": "healthy",
        "llm_providers": check_llm_health()
    }


@router.post("/anomaly-check", response_model=AnomalyCheckResponse)
def check_claim_anomalies(payload: AnomalyCheckRequest):
    """
    Evaluates a claim using IsolationForest and heuristic rules to detect repeat claims,
    helper velocity spikes, and demographic/income statistical anomalies.
    """
    res = detect_claim_anomalies(payload.claim_data, payload.historical_claims)
    return AnomalyCheckResponse(
        is_anomaly=res["is_anomaly"],
        anomaly_score=res["anomaly_score"],
        flags=res["flags"],
        reasons_en=res["reasons_en"],
        reasons_ur=res["reasons_ur"],
        metrics=res["metrics"]
    )


@router.get("/scam-map")
def get_scam_map(days: int = 7):
    """
    Returns live threat intelligence feed, regional cluster coordinates,
    category distribution, and temporal scam trends across Sindh & Karachi districts.
    """
    return generate_scam_map_feed(days=days)


@router.get("/eval-summary")
def get_eval_summary():
    """
    Returns aggregated evaluation metrics, accuracy scores, confusion matrix,
    subsystem latency benchmarks, and threshold sweep expected cost curves.
    """
    return get_evaluation_dashboard_metrics()


@router.post("/sync-offline-batch")
def sync_offline_batch(payload: OfflineSyncBatchRequest):
    """
    Synchronizes cases queued locally on a helper's phone when connectivity restores.
    Provides idempotency deduplication, offline intake extraction, and pipeline routing.
    """
    return process_offline_sync_batch(
        helper_id=payload.helper_id,
        batch_id=payload.batch_id,
        queued_cases=payload.queued_cases,
        client_timestamp=payload.client_timestamp
    )

