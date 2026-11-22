"""
Adversarial Test Suite M: Multi-Tier LLM Provider Fallback & Resilience.
Tests L01 - L07: Evaluates upstream provider failures (HTTP 429, timeout, malformed JSON,
empty responses), seamless tier degradation, and deterministic safety guarantees.
"""
from unittest.mock import patch

from services.ai.router import check_llm_health, route_llm


def test_l01_primary_provider_429_rate_limit_fallback():
    """L01: Primary provider returns HTTP 429 Rate Limit; router falls back to secondary or safety."""
    messages = [{"role": "user", "content": "Hello"}]

    with patch("services.ai.router.call_groq") as mock_groq:
        mock_groq.side_effect = RuntimeError("HTTP 429: Too Many Requests (Rate limit reached)")

        # Must not raise an exception; degrades gracefully
        res = route_llm(messages, use_cache=False)
        assert res["provider"] in ("google/gemini-1.5-flash", "deterministic_safety_fallback")
        assert "content" in res


def test_l02_primary_provider_timeout_fallback():
    """L02: Primary provider times out; router catches timeout and triggers fallback."""
    messages = [{"role": "user", "content": "Test timeout"}]

    with patch("services.ai.router.call_groq") as mock_groq:
        mock_groq.side_effect = TimeoutError("Groq upstream connection timed out after 10.0s")

        res = route_llm(messages, use_cache=False)
        assert res["provider"] != "groq"
        assert len(res["content"]) > 0


def test_l03_primary_provider_malformed_response():
    """L03: Primary provider returns malformed / unparsable response."""
    messages = [{"role": "user", "content": "Test malformed"}]

    with patch("services.ai.router.call_groq") as mock_groq:
        mock_groq.side_effect = ValueError("Corrupted JSON body returned by upstream")

        res = route_llm(messages, use_cache=False)
        assert "content" in res


def test_l04_primary_provider_empty_response():
    """L04: Primary provider returns empty response."""
    messages = [{"role": "user", "content": "Test empty"}]

    with patch("services.ai.router.call_groq") as mock_groq:
        mock_groq.side_effect = ValueError("Empty choices returned")

        res = route_llm(messages, use_cache=False)
        assert res["provider"] in ("google/gemini-1.5-flash", "deterministic_safety_fallback")


def test_l05_all_online_providers_fail_deterministic_safety_guarantee():
    """L05: Every upstream cloud provider fails; system delivers deterministic offline response without crashing."""
    messages = [{"role": "user", "content": "Test all fail"}]

    with patch("services.ai.router.GROQ_API_KEY", "gsk_test"), \
         patch("services.ai.router.GEMINI_API_KEY", "AIzaSy_test"), \
         patch("services.ai.router.call_groq") as mock_groq, \
         patch("services.ai.router.call_gemini") as mock_gemini:
        mock_groq.side_effect = ConnectionError("No internet to Groq")
        mock_gemini.side_effect = ConnectionError("No internet to Gemini")

        res = route_llm(messages, use_cache=False)

        assert res["provider"] == "deterministic_safety_fallback"
        assert "human officer review" in res["content"]
        assert len(res["errors"]) >= 1


def test_l06_response_caching_accelerates_identical_prompts():
    """L06: Second identical prompt returns from cache with zero upstream latency."""
    messages = [{"role": "user", "content": "Unique prompt for caching test"}]

    with patch("services.ai.router.GROQ_API_KEY", "gsk_test"), \
         patch("services.ai.router.call_groq", return_value={"content": "cached answer", "model": "llama-3"}):
        res1 = route_llm(messages, use_cache=True)
        res2 = route_llm(messages, use_cache=True)

        assert res2.get("cached") is True
        assert res1["content"] == res2["content"]


def test_l07_llm_health_check_returns_structured_diagnostics():
    """L07: check_llm_health reports diagnostics for configured endpoints without crashing."""
    health = check_llm_health()
    assert isinstance(health, dict)
    assert "groq" in health
    assert "gemini" in health
