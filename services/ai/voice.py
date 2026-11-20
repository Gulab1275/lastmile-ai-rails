"""
Urdu Voice Pipeline (Challenge 07: Works for Everyone).
Speech-to-Text: Whisper-large-v3 via Groq (handles Urdu natively).
Text-to-Speech: edge-tts (Urdu: ur-PK-UzmaNeural / ur-PK-AsadNeural) with MD5 audio disk caching.
"""
import os
import io
import re
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

# Whisper Context Priming Prompt (biases away from music/ambient noise)
URDU_WHISPER_PROMPT = "پاکستانی شہری کی آواز، احساس و بے نظیر پروگرام، نام، شناختی کارڈ، آمدنی، بیوہ کا امدادی فارم۔"

# Hallucination tokens emitted by Whisper on silence or background room noise
SILENCE_HALLUCINATIONS = {
    "موسیقا", "موسیقی", "موسیقی۔", "موسیقی!", "موسیقا۔", "موسیقی؟",
    "[موسیقی]", "(موسیقی)", "[music]", "(music)", "music",
    "thank you", "subtitles", "subtitle", "...", "۔۔۔", "آپ"
}

def detect_audio_format(audio_bytes: bytes, filename: Optional[str] = None) -> tuple[str, str]:
    """Detects audio file extension and MIME type from header magic bytes or filename."""
    if filename:
        ext = filename.lower().split(".")[-1]
        if ext in ("webm", "weba"):
            return "input.webm", "audio/webm"
        elif ext == "wav":
            return "input.wav", "audio/wav"
        elif ext == "ogg":
            return "input.ogg", "audio/ogg"
        elif ext in ("m4a", "mp4"):
            return "input.m4a", "audio/m4a"
        elif ext == "mp3":
            return "input.mp3", "audio/mp3"

    # Magic byte sniffing
    if audio_bytes.startswith(b"\x1aE\xdf\xa3"):
        return "input.webm", "audio/webm"
    elif audio_bytes.startswith(b"RIFF"):
        return "input.wav", "audio/wav"
    elif audio_bytes.startswith(b"OggS"):
        return "input.ogg", "audio/ogg"
    elif b"ftyp" in audio_bytes[:16]:
        return "input.m4a", "audio/m4a"
    
    # Default to MP3
    return "input.mp3", "audio/mp3"

def transcribe(
    audio_bytes: bytes,
    language: str = "ur",
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes Urdu / English speech to text using Groq Whisper-large-v3.
    Supports WebM (from browser MediaRecorder), WAV, MP3, OGG, and M4A.
    """
    if not audio_bytes:
        return {"text": "", "language": language, "confidence": 0.0}

    from groq import Groq
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is required for voice transcription")

    client = Groq(api_key=GROQ_API_KEY)
    
    # Auto-detect audio format
    detected_name, detected_mime = detect_audio_format(audio_bytes, filename)
    file_tuple = (detected_name, io.BytesIO(audio_bytes), content_type or detected_mime)
    
    try:
        transcription = client.audio.transcriptions.create(
            file=file_tuple,
            model="whisper-large-v3",
            language=language if language != "auto" else None,
            prompt=URDU_WHISPER_PROMPT if language == "ur" else None,
            temperature=0.0
        )
        raw_text = transcription.text.strip()
        
        # Check for silence or Whisper hallucinations on low/ambient room sound
        clean_norm = re.sub(r"[^\w\s]", "", raw_text).strip()
        is_silence = (
            not raw_text
            or raw_text.lower() in SILENCE_HALLUCINATIONS
            or clean_norm in ("موسیقا", "موسیقی", "music")
            or len(clean_norm) <= 1
        )
        
        if is_silence:
            return {
                "text": "",
                "language": language,
                "confidence": 0.0,
                "format": detected_name.split(".")[-1],
                "is_silent": True,
                "message": "کوئی واضح آواز سنائی نہیں دی (No speech detected)"
            }

        confidence = 0.95 if len(raw_text) > 5 else 0.75
        return {
            "text": raw_text,
            "language": language,
            "confidence": confidence,
            "format": detected_name.split(".")[-1],
            "is_silent": False,
            "message": "کامیابی سے ٹرانسکرائب ہو گیا"
        }
    except Exception as e:
        return {
            "text": "",
            "language": language,
            "confidence": 0.0,
            "is_silent": True,
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
