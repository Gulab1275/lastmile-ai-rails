"""
Urdu Voice Pipeline (Challenge 07: Works for Everyone).
Speech-to-Text: Whisper-large-v3 via Groq (handles Urdu natively).
Text-to-Speech: edge-tts (Urdu: ur-PK-UzmaNeural / ur-PK-AsadNeural) with MD5 audio disk caching.
"""
import os
import io
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "audio_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Default Urdu voice in edge-tts
URDU_VOICE = "ur-PK-UzmaNeural"
ENGLISH_VOICE = "en-US-JennyNeural"

def transcribe(audio_bytes: bytes, language: str = "ur") -> Dict[str, Any]:
    """
    Transcribes Urdu / English speech to text using Groq Whisper-large-v3.
    """
    if not audio_bytes:
        return {"text": "", "language": language, "confidence": 0.0}

    from groq import Groq
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for voice transcription")

    client = Groq(api_key=GROQ_API_KEY)
    
    # Send audio bytes as in-memory file tuple
    file_tuple = ("input.mp3", io.BytesIO(audio_bytes), "audio/mp3")
    
    try:
        transcription = client.audio.transcriptions.create(
            file=file_tuple,
            model="whisper-large-v3",
            language=language if language != "auto" else None,
            temperature=0.0
        )
        text = transcription.text.strip()
        confidence = 0.95 if len(text) > 5 else 0.70
        return {
            "text": text,
            "language": language,
            "confidence": confidence
        }
    except Exception as e:
        return {
            "text": "",
            "language": language,
            "confidence": 0.0,
            "error": str(e)
        }

async def _synthesize_async(text: str, voice: str, cache_file: Path) -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(cache_file))
    with open(cache_file, "rb") as f:
        return f.read()

def synthesize(text: str, lang: str = "ur") -> bytes:
    """
    Synthesizes Urdu or English text to MP3 audio bytes.
    Caches output audio files on disk by text MD5 hash to avoid repeated calls.
    """
    if not text or not text.strip():
        return b""

    # MD5 caching
    cache_key = hashlib.md5(f"{lang}:{text}".encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.mp3"
    
    if cache_file.exists():
        with open(cache_file, "rb") as f:
            return f.read()

    voice = URDU_VOICE if lang == "ur" else ENGLISH_VOICE
    
    try:
        # Run async in synchronous context
        return asyncio.run(_synthesize_async(text, voice, cache_file))
    except Exception as e:
        print(f"edge-tts error: {e}")
        return b""
