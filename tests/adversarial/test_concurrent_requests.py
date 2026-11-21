"""
Adversarial Test Suite N: Performance & Concurrency Load Testing.
Runs controlled concurrent load tests (10, 25, 50, 100 requests) against:
- Scam classifier
- Document OCR
- Policy RAG search
- Database queries
Calculates: Average, P95, P99 latency, error rate, and throughput.
"""
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from services.ai.ocr import compute_blur_score
from services.ai.rag import search_policy_chunks
from services.ai.scam import classify_message


def _run_load_test(target_fn, concurrency_level: int, *args):
    latencies = []
    errors = 0

    t_start = time.time()
    with ThreadPoolExecutor(max_workers=min(concurrency_level, 20)) as executor:
        futures = [executor.submit(target_fn, *args) for _ in range(concurrency_level)]
        for f in futures:
            try:
                t0 = time.time()
                f.result()
                latencies.append((time.time() - t0) * 1000)
            except Exception:
                errors += 1

    total_time = time.time() - t_start
    lat_arr = np.array(latencies) if latencies else np.array([0.0])

    return {
        "concurrency": concurrency_level,
        "completed": len(latencies),
        "errors": errors,
        "error_rate": errors / concurrency_level,
        "avg_ms": float(np.mean(lat_arr)),
        "p95_ms": float(np.percentile(lat_arr, 95)),
        "p99_ms": float(np.percentile(lat_arr, 99)),
        "total_time_s": total_time,
        "rps": len(latencies) / max(0.001, total_time)
    }


def test_n01_scam_classifier_10_concurrent_requests():
    """N01: 10 concurrent requests to scam classification."""
    metrics = _run_load_test(classify_message, 10, "Mubarak ho! 25000 grant mila hai bit.ly/test")
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 250.0


def test_n02_scam_classifier_25_concurrent_requests():
    """N02: 25 concurrent requests to scam classification."""
    metrics = _run_load_test(classify_message, 25, "Mubarak ho! 25000 grant mila hai bit.ly/test")
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 300.0


def test_n03_scam_classifier_50_concurrent_requests():
    """N03: 50 concurrent requests to scam classification."""
    metrics = _run_load_test(classify_message, 50, "Mubarak ho! 25000 grant mila hai bit.ly/test")
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 400.0


def test_n04_scam_classifier_100_concurrent_requests():
    """N04: 100 concurrent requests to scam classification."""
    metrics = _run_load_test(classify_message, 100, "Mubarak ho! 25000 grant mila hai bit.ly/test")
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 500.0


def test_n05_ocr_blur_calculation_25_concurrent_requests():
    """N05: 25 concurrent image blur calculations."""
    dummy_img = Image.new("RGB", (200, 150), color=(128, 128, 128))
    metrics = _run_load_test(compute_blur_score, 25, dummy_img)
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 100.0


def test_n06_rag_hybrid_retrieval_10_concurrent_requests():
    """N06: 10 concurrent policy RAG retrieval queries."""
    metrics = _run_load_test(search_policy_chunks, 10, "income limit widow relief grant")
    assert metrics["errors"] == 0


def test_n07_api_gateway_concurrent_health_checks(client: TestClient):
    """N07: 50 concurrent requests to API health endpoint."""
    def get_health():
        return client.get("/api/v1/health")

    metrics = _run_load_test(get_health, 50)
    assert metrics["errors"] == 0
    assert metrics["p95_ms"] < 150.0
