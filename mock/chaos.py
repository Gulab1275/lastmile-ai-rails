"""
Chaos engineering helper to simulate unreliable public rails, slow network, timeouts, and 500 errors.
"""
import asyncio
import os
from typing import Optional

from fastapi import HTTPException

from services.shared.schemas import ChaosMode


class ChaosTriggeredException(HTTPException):
    def __init__(self, detail: str = "Simulated public rail failure (Chaos Mode active)"):
        super().__init__(status_code=500, detail=detail)


async def apply_chaos(chaos_mode: Optional[str] = None, latency_ms: Optional[int] = None):
    """
    Applies chaos effects if requested via query param or environment variable.
    Supported modes:
    - none: pass-through normally
    - 500: raise HTTP 500 server error
    - timeout: simulate severe server timeout (asyncio sleep then error)
    - slow: simulate high network latency
    """
    mode = chaos_mode or os.getenv("MOCK_CHAOS_MODE", "none").lower()
    default_latency = int(os.getenv("MOCK_CHAOS_LATENCY_MS", "1500"))
    delay_ms = latency_ms if latency_ms is not None else default_latency

    if mode == ChaosMode.STATUS_500.value:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "PUBLIC_RAIL_UNAVAILABLE",
                "message_en": "Simulated DPI rail 500 Internal Error (Chaos Mode)",
                "message_ur": "عوامی ڈیجیٹل سروس عارضی طور پر بند ہے۔ برائے مہربانی بعد میں دوبارہ کوشش کریں۔"
            }
        )
    elif mode == ChaosMode.TIMEOUT.value:
        await asyncio.sleep(min(delay_ms / 1000.0, 5.0))
        raise HTTPException(
            status_code=504,
            detail={
                "code": "GATEWAY_TIMEOUT",
                "message_en": "Simulated DPI rail gateway timeout (Chaos Mode)",
                "message_ur": "سروس کا رابطہ منقطع ہو گیا۔ ٹائم آؤٹ۔"
            }
        )
    elif mode == ChaosMode.SLOW.value:
        await asyncio.sleep(delay_ms / 1000.0)
