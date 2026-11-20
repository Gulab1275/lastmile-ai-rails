# Rahbar — Runtime Context (CONTEXT.md)
*Current operational status, active sprint/block, immediate priorities, and integration states.*
*Last updated: 2026-11-20 (Phase 3 Complete: AI Services, Anomaly Detection & Creative Rails Unified)*

---

## 1. Current Phase: Phase 3 (AI, Observability & Creative Rails) Complete
* **Status:** **100% OPERATIONAL & VERIFIED**
* **Test Suite:** **36 / 36 PASSED** (11.30s execution time)
* **API Endpoints:** **40 documented endpoints** in [`docs/openapi.json`](file:///e:/lastmile-ai-rails/docs/openapi.json) (now including 12 dedicated `/api/v1/ai/` endpoints).
* **Cross-Team Alignment:** Full backward compatibility maintained with Mahandar's FastAPI backend and Gulab's frontend PWA contract.

---

## 2. Integrated Architecture & AI Capabilities Status

| Area | Component | Implementation Status | Test Status |
| :--- | :--- | :--- | :--- |
| **API & Security** | FastAPI Gateway (`services/api/`) | RBAC, JWT tokens, Argon2id, rate limiting (`slowapi`). | **PASSED** |
| **Consent Gateway** | `services/api/engine/consent_gateway.py` | Real-time scope check & immediate 403 block on revocation. | **PASSED** |
| **Audit Ledger** | `services/api/engine/audit_log.py` | Cryptographic SHA-256 hash chaining & tamper detection. | **PASSED** |
| **Rules Engine** | `services/api/engine/rules_engine.py` | Dynamic versioned JSON rules, trace generation, zero-downtime publish. | **PASSED** |
| **Decision Engine** | `services/api/engine/decision_engine.py` | Cost-matrix routing, weakest-link confidence ($\min(\text{components})$). | **PASSED** |
| **Mock Rails** | `mock/nadra.py`, `mock/raast.py`, `mock/complaints.py` | Gated approval token, idempotency keys, chaos modes (timeout, 500, slow). | **PASSED** |
| **Digital Twin** | `services/api/routes/digital_twin.py` | Historical case replay against draft rules before publishing. | **PASSED** |
| **Database** | `db/` (Supabase Postgres) | 13 tables + `pgvector` provisioned; pooling verified. | **PASSED** |
| **AI LLM Router** | `services/ai/router.py` | Groq (`qwen/qwen3.8-27b`) primary at 131ms + Gemini fallback. | **PASSED** |
| **Urdu Voice** | `services/ai/voice.py` | Whisper large-v3 STT + `edge-tts` Urdu (`ur-PK-UzmaNeural`). | **PASSED** |
| **Scam Model** | `services/ai/scam.py` | Calibrated scikit-learn TF-IDF + Logistic Regression model. | **PASSED** |
| **OCR Pipeline** | `services/ai/ocr.py` | Laplacian blur detection (2072 vs 0.20) + tamper scoring. | **PASSED** |
| **Form Extraction** | `services/ai/forms.py` | Conversational Urdu/English intake to validated Pydantic model. | **PASSED** |
| **LangGraph Agent** | `services/ai/agent.py` | Checkpointed claim graph with gated disbursement tool. | **PASSED** |
| **Anomaly Detection**| `services/ai/anomaly.py` | Task N13: IsolationForest + helper velocity + duplicate bursts. | **PASSED** |
| **Scam Map Threat Feed**| `services/ai/scam_map.py` | Karachi/Sindh GPS hotspot clusters + category taxonomy. | **PASSED** |
| **Evaluation Dashboard**| `services/ai/eval_dashboard.py`| Precision/recall, latency benchmarks, cost curve sweeps. | **PASSED** |
| **Offline Sync Batch** | `services/ai/sync.py` | Low-bandwidth idempotency deduplication & batch intake. | **PASSED** |
| **Seed Generator** | `seed/run_seed.py` | 200 citizens, 6 demo role accounts, intentional edge cases. | **PASSED** |

---

## 3. Dedicated AI & Agent REST Endpoints

All accessible under `/api/v1/ai/`:
1. `POST /scam-check`: Real-time phishing and fake relief message detection.
2. `POST /ocr`: Laplacian blur gate and tamper scoring for document uploads.
3. `POST /voice/stt`: Groq Whisper large-v3 Urdu and English transcription.
4. `POST /voice/tts`: Edge-TTS natural Urdu speech audio synthesis with caching.
5. `POST /ask`: RAG policy question answering with official page citations.
6. `POST /extract-form`: Conversational speech extraction into Pydantic schema.
7. `POST /agent/run`: LangGraph state machine orchestrating claim decisions.
8. `POST /anomaly-check`: IsolationForest outlier detection and repeat burst flags.
9. `GET /scam-map`: Threat intelligence feed with regional GPS coordinates.
10. `GET /eval-summary`: Observability metrics, confusion matrix, and cost sweeps.
11. `POST /sync-offline-batch`: Offline-first queue sync with duplicate prevention.
12. `GET /health`: Upstream LLM provider latency and status telemetry.

---

## 4. Git Status & Deployment Readiness
* **Branch:** `main`
* **Remote State:** Successfully synchronized with `origin/main` (`6d8c29f..fc669f6`).
* **OpenAPI Contract:** [`docs/openapi.json`](file:///e:/lastmile-ai-rails/docs/openapi.json) published with 40 routes for frontend consumption.
* **Test Verification:** 36 / 36 tests passing (100%).
* **Current Status:** Working tree clean. Ready for next phase / UI integration with Gulab.
