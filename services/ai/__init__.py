"""
Services AI Package for Rahbar.
Owned by Naresh (AI Core & Agents).

Exposes the clean contract functions directly imported by Mahandar's FastAPI backend:
1. extract_documents(files)
2. classify_message(text)
3. transcribe(audio_bytes, language)
4. synthesize(text, lang)
5. ask_policy(question)
6. run_claim_agent(case_id)
7. extract_claim_form(transcript)
8. detect_claim_anomalies(claim, historical_claims)
9. generate_scam_map_feed(days, reported_scams)
10. get_evaluation_dashboard_metrics()
11. process_offline_sync_batch(helper_id, batch_id, queued_cases)
"""

from .ocr import extract_documents
from .scam import classify_message
from .voice import transcribe, synthesize
from .rag import ask_policy
from .pipeline import run_claim_agent, evaluate_claim_pipeline
from .matcher import resolve_identity, normalize_name, compute_name_similarity
from .router import route_llm, check_llm_health
from .forms import extract_claim_form
from .anomaly import detect_claim_anomalies
from .scam_map import generate_scam_map_feed
from .eval_dashboard import get_evaluation_dashboard_metrics
from .sync import process_offline_sync_batch

__all__ = [
    "extract_documents",
    "classify_message",
    "transcribe",
    "synthesize",
    "ask_policy",
    "run_claim_agent",
    "evaluate_claim_pipeline",
    "resolve_identity",
    "normalize_name",
    "compute_name_similarity",
    "route_llm",
    "check_llm_health",
    "extract_claim_form",
    "detect_claim_anomalies",
    "generate_scam_map_feed",
    "get_evaluation_dashboard_metrics",
    "process_offline_sync_batch",
]
