# Rahbar — Runtime Context (CONTEXT.md)
*Current operational status, active sprint/block, immediate priorities, and integration states.*
*Last updated: 2026-11-20 (Block 0)*

---

## 1. Current Phase: Block 0 — Contract & Foundations (T+0 to T+3)
* **Goal of this block:** Lock down contracts, initialize database foundations, verify services, and enable all 3 engineers to build independently without waiting or blocking.
* **Exit Gate Criteria:** 
  - `services/shared/schemas.py` frozen.
  - Supabase database initialized with core tables.
  - Mahandar's `/health` endpoint live on AWS EC2.
  - Gulab generating typed client from OpenAPI JSON.

---

## 2. Immediate Next Actions for Naresh

### Step 1: Shared Schema Contract (`services/shared/schemas.py`)
* Create the shared Pydantic models:
  * `DecisionResponse` (case_id, route, confidence, components, missing, reason_simple, rule_version)
  * `ComponentScores` (identity, ocr, authenticity, rules_complete, scam_safety)
  * `ClaimCreate` / `ClaimDetail`
  * `ErrorResponse` (code, message_en, message_ur)
  * Function signatures for the 6 AI functions exposed to `services/api`.

### Step 2: Supabase Database Layer (`db/`)
* Create `db/connection.py` for Supabase PostgreSQL pooling and keep-alive.
* Create `db/models.py` (SQLAlchemy / SQL schema):
  * `users`, `citizens`, `consents`, `cases`, `documents`, `decisions`, `rule_versions`, `review_items`, `audit_log`, `scam_messages`, `eval_results`, `policy_chunks`.
* Enable `pgvector` extension on Supabase.

### Step 3: LiteLLM Router (`services/ai/router.py`)
* Configure multi-tier fallback: Groq `llama-3.3-70b-versatile` $\to$ Gemini $\to$ OpenRouter.
* Add unit test with provider failure simulation.

### Step 4: Synthetic Seed Generator (`seed/run_seed.py`)
* Build dataset generator:
  * 200 mock citizens with name variants (Muhammad/Mohd), duplicates, and missing fields.
  * 200+ labelled scam/legit SMS & WhatsApp messages (Urdu, Roman Urdu, English).
  * Mock CNIC and utility bill image templates.

---

## 3. Team Integration Status

| Module / Team Member | Status | Blockers | Notes |
| :--- | :--- | :--- | :--- |
| **Naresh** (AI & Supabase) | **Active / Ready** | None | Groq & Supabase credentials verified. Ready to create `services/shared/schemas.py` and `db/models.py`. |
| **Mahandar** (API & AWS) | Waiting on Contract | Needs `schemas.py` | Will consume `services/shared/schemas.py` to expose `/health` and OpenAPI spec. |
| **Gulab** (Next.js PWA) | Ready for Shell | Needs OpenAPI spec | Can use `schemas.py` as TypeScript reference for mock fixtures. |

---

## 4. Environment Quick Reference
* **OS:** Windows 10/11
* **Active Working Directory:** `e:\lastmile-ai-rails`
* **Git Remote:** `https://github.com/Naresh-Kumar17/lastmile-ai-rails.git` (`origin/main`)
* **Local Python:** Python 3.14.7 64-bit
* **Secrets Location:** `.env` (Never commit to Git)
