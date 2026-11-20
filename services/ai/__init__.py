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
"""

from .ocr import extract_documents
from .scam import classify_message
from .voice import transcribe, synthesize
from .rag import ask_policy
from .pipeline import run_claim_agent, evaluate_claim_pipeline
from .matcher import resolve_identity, normalize_name, compute_name_similarity
from .router import route_llm, check_llm_health

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
    "check_llm_health"
]
