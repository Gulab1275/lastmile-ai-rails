# Rahbar — Project Memory (MEMORY.md)
*Persistent architectural memory, key decisions, team conventions, and project history.*
*Last updated: 2026-11-20 (Block 0)*

---

## 1. Project Overview & North Star
* **Project Name:** Rahbar (The Last Mile: AI on Public Rails)
* **Hackathon:** Coder's Cup '26 · AI Hackathon
* **Repository:** `https://github.com/Naresh-Kumar17/lastmile-ai-rails.git`
* **Core Problem:** Helping community helpers, illiterate citizens (widows), and shopkeepers file mock Relief Cash Support claims in Urdu through voice, low-bandwidth resilience, scam screening, and auditable, deterministic public rails.

---

## 2. Team Division of Labor (Zero-Conflict Contract)

| Engineer | Primary Role | Dedicated Folders | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Mahandar** | Backend & AWS Lead | `services/api/`<br/>`mock/`<br/>`infra/`<br/>`.github/` | AWS EC2 (t3.small), Docker Compose, Caddy (HTTPS + DuckDNS), FastAPI gateway, 5-role RBAC, JWT auth, Rules Engine, Decision Router, Consent Gateway, Mock services (NADRA, Raast). |
| **Naresh** | AI Core & Supabase Lead | `db/`<br/>`seed/`<br/>`services/ai/` | Supabase Postgres + `pgvector` provisioning, SQLAlchemy models, Alembic migrations, synthetic seed script (200 citizens, scam SMS, mock IDs), LiteLLM router, OCR, Urdu voice (STT/TTS), RAG, LangGraph agent, evaluation harness. |
| **Gulab** | Frontend & PWA Lead | `apps/web/` | Next.js PWA, Urdu RTL layout (Noto Nastaliq), voice-first touch UI, 40-family switcher, offline IndexedDB queue, MSW mock fixtures, Vercel deployment. |
| **Shared** | Frozen Contract | `services/shared/` | `schemas.py` — Pydantic models for claims, decisions, components, errors, and AI function signatures. |

---

## 3. Core Architectural Invariants (Non-Negotiables)
1. **The LLM never makes the approval decision.** Deterministic rules plus a calibrated ML score decide. The LLM only extracts fields, explains, and answers questions.
2. **Confidence is the weakest link:**
   $$\text{overall} = \min(\text{identity}, \text{ocr}, \text{authenticity}, \text{rules\_complete}, \text{scam\_safety})$$
3. **The system never auto-rejects:** Clean claims auto-approve under threshold; ambiguous claims ask for more proof; low confidence routes to human officers with handoff notes.
4. **Consent Gateway:** Every read of citizen data passes through `gateway.read(actor, citizen, scope)`. Revocation blocks access on the very next call.
5. **Multi-tier LLM fallback:** Groq (`Llama-3-70B`) $\to$ Gemini $\to$ OpenRouter free $\to$ Bedrock fallback.
6. **No secrets in Git:** All API keys, passwords, and tokens stay strictly in `.env`.

---

## 4. Verified Services & Infrastructure Status
* **Supabase Project:**
  * Ref: `rhlvnyqgrbjsvlbzljhz`
  * URL: `https://rhlvnyqgrbjsvlbzljhz.supabase.co`
  * Status: **Verified & Active (HTTP 200)**
  * PostgreSQL Database: Configured in `.env`
* **Groq API:**
  * Key: Configured in `.env`
  * Status: **Verified & Active (HTTP 200)**
  * Models available: `whisper-large-v3`, `whisper-large-v3-turbo`, `llama-3.x`
* **Gemini API:**
  * Key: Configured in `.env` (Fallback LLM)

---

## 5. Milestone & Decision Log
* **2026-11-20 (Block 0):**
  * PRD finalized in pure Markdown ([`Rahbar_PRD_and_Build_Plan.md`](file:///e:/lastmile-ai-rails/Rahbar_PRD_and_Build_Plan.md)).
  * All binary PDF files removed from repository.
  * `.gitignore` and `.env.example` created, committed, and pushed to `origin/main`.
  * Local `.env` initialized and tested against live Groq and Supabase endpoints.
  * Project memory (`MEMORY.md`) and runtime context (`CONTEXT.md`) initialized.
