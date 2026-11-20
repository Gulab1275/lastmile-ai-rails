# Rahbar — Runtime Context (CONTEXT.md)
*Current operational status, active sprint/block, immediate priorities, and integration states.*
*Last updated: 2026-11-20 (Phase 4 Complete: Demo Runner, Keep-Alive Heartbeat, Judging Guide & E2E Suite)*

---

## 1. Current Phase: Phase 4 (Judging Verification & E2E Test Suite) Complete
* **Status:** **100% OPERATIONAL & VERIFIED**
* **Test Suite:** **37 / 37 PASSED** (10.51s execution time)
* **Presentation Runner:** [`scripts/demo_runner.py`](file:///e:/lastmile-ai-rails/scripts/demo_runner.py) executes all 12 demo steps across all 8 challenges with 100% assertions passing.
* **Keep-Alive Script:** [`scripts/keepalive_ping.py`](file:///e:/lastmile-ai-rails/scripts/keepalive_ping.py) keeps Supabase Postgres warm and monitors pool connections.
* **Judging Documentation:** [`docs/JUDGING_WALKTHROUGH.md`](file:///e:/lastmile-ai-rails/docs/JUDGING_WALKTHROUGH.md) provides an executive challenge-to-code mapping for evaluators.
* **API Endpoints:** 40 documented endpoints in [`docs/openapi.json`](file:///e:/lastmile-ai-rails/docs/openapi.json).

---

## 2. Integrated Architecture & Verification Status

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
| **Demo Runner** | `scripts/demo_runner.py` | 12-step presentation script covering all 8 challenges. | **PASSED** |
| **Keep-Alive Ping** | `scripts/keepalive_ping.py` | Supabase heartbeat & connection pool monitor. | **PASSED** |

---

## 3. Git Status & Deployment Readiness
* **Branch:** `main`
* **Local State:** Phase 4 completed; 37 tests passing.
* **Directives:** Awaiting explicit instruction from Naresh before running `git push origin main`.
