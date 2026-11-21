"""
Multi-tier LLM Router with Caching and Fallback.
Tier 1: Groq (qwen/qwen3.8-27b / openai/gpt-oss-120b) - primary, ultra-fast, multilingual.
Tier 2: Google Gemini (gemini-1.5-flash) - secondary fallback.
Tier 3: Deterministic Safety Fallback - offline / zero-rate-limit guaranteed fallback.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Supported Groq chat models in priority order
GROQ_MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

# In-memory response cache
_RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}

def _cache_key(messages: List[Dict[str, str]], temperature: float) -> str:
    raw = json.dumps({"m": messages, "t": temperature}, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()

def call_groq(messages: List[Dict[str, str]], temperature: float = 0.2) -> Dict[str, Any]:
    from groq import Groq
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    client = Groq(api_key=GROQ_API_KEY)

    last_err = None
    for model_name in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
                timeout=10.0
            )
            return {
                "content": response.choices[0].message.content,
                "model": model_name
            }
        except Exception as e:
            last_err = e
            continue
    raise last_err or ValueError("All Groq models failed")

def call_gemini(messages: List[Dict[str, str]], temperature: float = 0.2) -> Dict[str, Any]:
    import urllib.request
    if not GEMINI_API_KEY or not GEMINI_API_KEY.startswith("AIzaSy"):
        raise ValueError("GEMINI_API_KEY is not a valid Google AI Studio key (must start with AIzaSy)")

    contents = []
    for msg in messages:
        role = "user" if msg["role"] in ["user", "system"] else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 1024}
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "RahbarApp/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        data = json.loads(resp.read().decode())
        candidates = data.get("candidates", [])
        if candidates:
            return {
                "content": candidates[0]["content"]["parts"][0]["text"],
                "model": "gemini-1.5-flash"
            }
        raise ValueError("Empty response from Gemini")

def route_llm(messages: List[Dict[str, str]], temperature: float = 0.2, use_cache: bool = True) -> Dict[str, Any]:
    """
    Executes chat completion with automatic fallback and caching.
    Returns: {"content": str, "provider": str, "cached": bool, "latency_ms": float}
    """
    key = _cache_key(messages, temperature)
    if use_cache and key in _RESPONSE_CACHE:
        cached = _RESPONSE_CACHE[key]
        return {**cached, "cached": True}

    start_time = time.time()
    errors = []

    # 1. Try Groq (Primary)
    if GROQ_API_KEY:
        try:
            res = call_groq(messages, temperature)
            latency = round((time.time() - start_time) * 1000, 2)
            result = {
                "content": res["content"],
                "provider": f"groq/{res['model']}",
                "cached": False,
                "latency_ms": latency
            }
            _RESPONSE_CACHE[key] = result
            return result
        except Exception as e:
            errors.append(f"Groq failed: {e}")

    # 2. Try Gemini (Secondary Fallback)
    if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIzaSy"):
        try:
            res = call_gemini(messages, temperature)
            latency = round((time.time() - start_time) * 1000, 2)
            result = {
                "content": res["content"],
                "provider": f"google/{res['model']}",
                "cached": False,
                "latency_ms": latency
            }
            _RESPONSE_CACHE[key] = result
            return result
        except Exception as e:
            errors.append(f"Gemini failed: {e}")

    # 3. Deterministic Safety Fallback (Guaranteed to never crash the live demo)
    latency = round((time.time() - start_time) * 1000, 2)
    fallback_content = "The automated relief assistant is currently offline. Your claim has been safely queued for human officer review."
    return {
        "content": fallback_content,
        "provider": "deterministic_safety_fallback",
        "cached": False,
        "latency_ms": latency,
        "errors": errors
    }

def check_llm_health() -> Dict[str, Any]:
    """Tests all providers and returns latency / status."""
    test_msg = [{"role": "user", "content": "Respond with 'OK'."}]
    status = {}

    # Groq test
    try:
        t0 = time.time()
        res = call_groq(test_msg)
        status["groq"] = {
            "status": "healthy",
            "model": res["model"],
            "latency_ms": round((time.time() - t0) * 1000, 2)
        }
    except Exception as e:
        status["groq"] = {"status": "unhealthy", "error": str(e)}

    # Gemini test
    if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AIzaSy"):
        try:
            t0 = time.time()
            res = call_gemini(test_msg)
            status["gemini"] = {
                "status": "healthy",
                "model": res["model"],
                "latency_ms": round((time.time() - t0) * 1000, 2)
            }
        except Exception as e:
            status["gemini"] = {"status": "unhealthy", "error": str(e)}
    else:
        status["gemini"] = {"status": "disabled", "note": "Requires Google AI Studio AIzaSy... key"}

    return status
