# Rahbar — Project Memory (MEMORY.md)
*Persistent architectural memory, key decisions, team conventions, and project history.*
*Last updated: 2026-11-20 (Phase 4 Complete: Demo Runner, Keep-Alive, Judging Guide & E2E Suite)*

---

## 1. Project Overview & North Star
* **Project Name:** Rahbar (The Last Mile: AI on Public Rails)
* **Hackathon:** Coder's Cup '26 · Hagrid's Hackathon (FAST-NUCES Karachi)
* **Repository:** `https://github.com/Naresh-Kumar17/lastmile-ai-rails.git`
* **Core Problem:** Assisting community helpers, illiterate citizens (widows), and shopkeepers file mock Relief Cash Support claims in Urdu through voice, low-bandwidth resilience, scam screening, and auditable, deterministic public rails.

---

## 2. Team Division of Labor (Zero-Conflict Contract)

| Engineer | Primary Role | Dedicated Folders | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Mahandar** | Backend & AWS Lead | `services/api/`<br/>`mock/`<br/>`infra/`<br/>`.github/` | AWS EC2 (t3.small), Docker Compose, Caddy (HTTPS + DuckDNS), FastAPI gateway, 5-role RBAC, JWT auth, Rules Engine, Decision Router, Consent Gateway, Mock services (NADRA, Raast). |
| **Naresh** | AI Core & Supabase Lead | `db/`<br/>`seed/`<br/>`services/ai/`<br/>`scripts/` | Supabase Postgres + `pgvector` provisioning, SQLAlchemy models, Alembic migrations, synthetic seed script (200 citizens, scam SMS, mock IDs), LiteLLM router, OCR, Urdu voice (STT/TTS), RAG, LangGraph agent, evaluation harness, anomaly detector, scam map aggregator, offline sync engine, demo runner, keep-alive heartbeat. |
| **Gulab** | Frontend & PWA Lead | `apps/web/` | Next.js PWA, Urdu RTL layout (Noto Nastaliq), voice-first touch UI, 40-family switcher, offline IndexedDB queue, MSW mock fixtures, Vercel deployment. |
| **Shared** | Frozen Contract | `services/shared/` | `schemas.py` — Pydantic models for claims, decisions, components, errors, AI function signatures, anomaly checks, and offline sync. |

---

## 3. Core Architectural Invariants (Non-Negotiables)
1. **The LLM never makes the approval decision.** Deterministic rules plus a calibrated ML score decide. The LLM only extracts fields, explains, and answers questions.
2. **Confidence is the weakest link:**
   $$\text{overall} = \min(\text{identity}, \text{ocr}, \text{authenticity}, \text{rules\_complete}, \text{scam\_safety})$$
3. **The system never auto-rejects:** Clean claims auto-approve under threshold (PKR 15,000 / 25,000); ambiguous claims ask for more proof; low confidence routes to human officers with handoff notes.
4. **Consent Gateway:** Every read of citizen data passes through `gateway.read(actor, citizen, scope)`. Revocation blocks access on the very next call (HTTP 403).
5. **Multi-tier LLM fallback:** Groq (`qwen/qwen3.8-27b`) $\to$ Gemini $\to$ Deterministic safety fallback.
6. **No secrets in Git:** All API keys, passwords, and tokens stay strictly in `.env`.
7. **Git Push Rule:** Never push to GitHub automatically; commit locally and wait for explicit instruction from Naresh.

---

## 4. Test Suite & Quality Status
* **Automated Pytest Suite:** **37/37 tests passing (100%)**
  * `test_demo_e2e.py`: Complete 12-step hackathon presentation & challenge verification.
  * `test_ai_services.py`: 12 automated tests for STT/TTS, OCR blur gate, scam classifier, RAG policy Q&A, form extraction, LangGraph agent, IsolationForest anomalies, scam map clusters, eval metrics, and offline batch deduplication.
  * `test_audit_hash_chain.py`: Tamper-evident SHA-256 blockchain ledger.
  * `test_auth_rbac.py`: 5-role JWT server-side RBAC enforcement.
  * `test_consent_gateway.py`: Instant revocation blocking and helper delegation.
  * `test_decision_engine.py`: Cost matrix, weakest-link routing, no auto-rejection.
  * `test_digital_twin.py`: Simulation replay against historical claims.
  * `test_mock_services_chaos.py`: NADRA fuzzy matching, Raast token gating, chaos modes (500, timeout).
  * `test_rules_engine.py`: Dynamic JSON rule publishing with zero downtime.
  * `test_e2e_integration.py`: Complete 12-step citizen intake to disbursement lifecycle.

---

## 5. Milestone & Decision Log
* **2026-11-20 (Block 0 & 1):**
  * PRD finalized in pure Markdown ([`Rahbar_PRD_and_Build_Plan.md`](file:///e:/lastmile-ai-rails/Rahbar_PRD_and_Build_Plan.md)).
  * Local `.env` initialized with verified Supabase and Groq keys.
  * 13 Supabase tables provisioned + `pgvector` enabled via `db/init_db.py`.
  * AI pipeline, Urdu STT/TTS, scam detector, and OCR blur/tamper scoring built in `services/ai/`.
  * Seed data populated in Supabase (200 citizens, 6 demo role accounts).
* **2026-11-20 (Phase 2 & 3):**
  * Built `services/ai/forms.py`: Structured Pydantic extraction from conversational Urdu.
  * Built `services/ai/agent.py`: LangGraph StateGraph claim workflow with session checkpointing and token-gated disbursements.
  * Built `services/ai/anomaly.py` (Task N13): Scikit-learn `IsolationForest` outlier detection + helper velocity spikes + duplicate burst screening.
  * Built `services/ai/scam_map.py`: Threat intelligence aggregator with Karachi/Sindh GPS hotspot clusters and tactical taxonomy.
  * Built `services/ai/eval_dashboard.py`: Observability metrics, confusion matrices, latency benchmarks, and cost sweep curves.
  * Built `services/ai/sync.py`: Offline-first batch synchronization protocol with idempotency keys.
  * Built `services/api/routes/ai.py`: 12 REST endpoints for all AI and agent capabilities.
  * Exported updated OpenAPI specification: 40 endpoints documented in [`docs/openapi.json`](file:///e:/lastmile-ai-rails/docs/openapi.json).
  * Pushed Phase 3 changes (5 atomic commits: `4abf9a3..77d17a9`) to GitHub `origin/main`.
* **2026-11-20 (Phase 4):**
  * Built `scripts/demo_runner.py`: Interactive 12-step presentation script covering all 8 hackathon challenges.
  * Built `scripts/keepalive_ping.py`: Supabase heartbeat ping and connection pool monitor.
  * Built `tests/test_demo_e2e.py`: Automated Pytest verification for the full 12-step presentation lifecycle (37/37 tests pass).
  * Authored [`docs/JUDGING_WALKTHROUGH.md`](file:///e:/lastmile-ai-rails/docs/JUDGING_WALKTHROUGH.md): Official judging rubric mapping all 8 challenges to code, endpoints, and verification steps.
