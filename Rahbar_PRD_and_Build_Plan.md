# Rahbar: PRD and Build Plan
**Coder's Cup '26 · AI Hackathon · The Last Mile: AI on Public Rails**  
**Team:** Mahandar (Backend Lead & AWS Infra) · Naresh (Agents, AI & Supabase Data Platform) · Gulab (Frontend & PWA)  
*PROTOTYPE ONLY. Every identity, payment, and data service is simulated. No real personal data anywhere.*

---

## 1. The One Sentence
We help a community helper (and the widows and shopkeepers she serves) apply for a mock Relief Cash Support claim, even though they cannot read the forms, have a weak connection, and keep receiving fake relief messages.

**Why this task:** The brief states that one deep task beats many thin ones. A relief claim naturally touches all eight hackathon challenges: identity with bad data, rules that change, money (cost of being wrong), scams, consent, accessibility, explainability, and resilient public rails.

| Persona | Role in System | What They Do |
| :--- | :--- | :--- |
| **Widow** | Citizen | Speaks in Urdu, uploads CNIC photo and utility bill, follows progress via icons and voice. |
| **Shopkeeper** | Citizen | Pastes or forwards a suspicious "relief payment" SMS/WhatsApp message and receives an instant scam verdict with explanations. |
| **Helper (40 families)** | Community Helper | Operates on a single shared phone, switches between families with 2 taps, manages separate granular consent for each. |
| **Reviewer** | Department Officer | Works the review queue sorted by priority and confidence; approves or rejects with mandatory written notes. |
| **Rule Owner** | Admin | Edits eligibility rules without writing code; tests and previews draft rules on past cases before publishing. |
| **Inspector** | Auditor | Read-only view of every AI decision, component confidence score, consent lifecycle change, and cryptographic hash-chained audit log. |

---

## 2. Design Principles (and Why)

1. **The LLM never makes the approval decision.** Deterministic rules plus a calibrated ML score decide. The LLM only extracts fields, explains, converses, and answers from policy documents.  
   *Why:* Decisions must be reproducible, auditable, and free from hallucinations. Free-tier LLMs are rate-limited and non-deterministic; a judge can replay any decision and get the exact same answer.
2. **Confidence is the weakest link, not the average.** Overall confidence is strictly the minimum of component confidences ($\text{overall} = \min(\text{components})$).  
   *Why:* A perfect 100% OCR read does not rescue a forged document or an unverified identity. One weak link must halt auto-approval.
3. **The system never auto-rejects.** It can auto-approve small, clean cases, ask for more proof, or hand off to a human officer. Rejections are always confirmed by a human officer.  
   *Why:* Blocking an eligible person in need carries severe real-world costs. A silent wrongful rejection is the worst failure mode.
4. **All data access goes through one Consent Gateway that writes the audit log.**  
   *Why:* Citizen consent withdrawal must instantly block access. If any query bypasses the gateway, the privacy guarantee is violated.
5. **Every free-tier dependency has a fallback.** LLM chain (`Groq -> Gemini -> OpenRouter free -> Bedrock`), OCR fallback, cached explanations, and pre-translated Urdu templates.  
   *Why:* A live demo is mandatory, and free tiers inevitably rate-limit at the worst moment.
6. **Contract-first architecture with clean team ownership boundaries.**  
   *Why:* Independent modules eliminate Git merge conflicts and remove the "frontend-waiting-on-backend" blocker.

---

## 3. Scope: What We Build

* **Roles (all 5):** Citizen, Helper, Officer, Admin, Auditor.
* **Core Foundation:** JWT authentication with server-side RBAC; dashboard with task progress; case management lifecycle; public REST API with Swagger docs; append-only hash-chained audit log; granular consent management (view, grant, withdraw, correct); mock external services (identity, payment, complaints); Supabase Postgres with Alembic migrations; structured logging and tests.
* **Platform Features:** Admin rule editor; officer review queue with priority/confidence sorting; low-bandwidth PWA mode with offline queue; rate limiting and error handling; background asynchronous jobs.
* **AI Features:**
  1. *RAG:* Answers from official policy PDFs with source page citations.
  2. *LangGraph Agent & Tool Calling:* Coordinates claim intake, mock identity checks, rules evaluation, and gated disbursements.
  3. *Classification & Routing:* Probabilistic scam and request classifier with calibrated confidence.
  4. *Computer Vision / OCR:* CNIC and utility bill OCR, blur detection, QR decoding, and tamper scoring.
  5. *Voice:* Urdu speech-to-text (Whisper) and text-to-speech (`edge-tts`).
  6. *Structured Outputs:* Pydantic-validated form extraction from conversational voice input.
  7. *Guardrails & Human Approval:* High-risk disbursements cryptographically gated; uncertain cases routed to officer queue.
  8. *Explainability:* Dual-view explanations (plain Urdu/English for citizens, full parameter trace for auditors).
  9. *Evaluation Dashboard:* Precision, recall, false-alarm rate, latency, and cost-threshold sweep curves.
* **Bonus (High Impact):** Digital Twin (replay past cases under a draft rule version to visualize approval rate impact before publishing).
* **Non-Goals:** Real NADRA/Raast integration, real paid SMS gateways, payments exceeding sandbox cap, languages beyond Urdu and English.

---

## 4. Conflict-Free Team Boundaries & Architecture

To ensure **zero Git merge conflicts** and allow Mahandar, Naresh, and Gulab to work completely independently in parallel, the architecture and repository ownership are partitioned cleanly:

```
rahbar/
├── apps/
│   └── web/                 # [GULAB] Next.js PWA, Tailwind, shadcn, Urdu RTL, PWA service worker
├── services/
│   ├── api/                 # [MAHANDAR] FastAPI gateway, routes, RBAC, rules engine, consent gateway, decision engine
│   ├── ai/                  # [NARESH] LiteLLM router, scam classifier, OCR pipeline, voice STT/TTS, RAG, LangGraph
│   └── shared/              # [SHARED CONTRACT] Frozen Pydantic schemas (case, decision, error, AI signatures)
├── db/                      # [NARESH] Supabase setup, Alembic migrations, database models, DB connection pooling
├── mock/                    # [MAHANDAR] Mock external services (NADRA, Raast, Complaints) with chaos switches
├── seed/                    # [NARESH] Synthetic citizens, scam messages, mock ID/bill images, policy PDFs, seed script
├── infra/                   # [MAHANDAR] AWS EC2 Dockerfile, docker-compose.yml, Caddyfile, deploy scripts, systemd
├── docs/                    # [SHARED] PRD, architecture diagrams, API notes, judging slides, eval reports
├── .env.example             # [SHARED / MAHANDAR & NARESH] Documented environment variables with no real secrets
├── .github/workflows/       # [MAHANDAR] CI workflow (lint ruff, test pytest, next build)
└── README.md                # [SHARED / GULAB & NARESH] Setup guide, Real vs Simulated table, demo accounts
```

### Team Ownership Matrix

| Area | Primary Owner | Dedicated Folder | Why This Prevents Conflicts |
| :--- | :--- | :--- | :--- |
| **AWS & Infrastructure** | **Mahandar** | `infra/`, `.github/workflows/` | Mahandar manages Docker Compose, Caddy HTTPS, EC2 instance, and CI without touching application code. |
| **API Gateway & Core Platform** | **Mahandar** | `services/api/`, `mock/` | Owns FastAPI endpoints, RBAC middleware, JWT auth, mock services, and business rules execution. |
| **Supabase & Database Platform** | **Naresh** | `db/`, `seed/` | Naresh provisions Supabase Postgres + `pgvector`, writes SQLAlchemy models, creates Alembic migrations, and manages seed data. |
| **AI, Voice & Agents** | **Naresh** | `services/ai/` | Naresh develops LiteLLM router, OCR, Whisper voice, scam model, RAG, LangGraph, and evaluation harness. |
| **Frontend & PWA** | **Gulab** | `apps/web/` | Gulab works 100% inside `apps/web/`, generating his client from the OpenAPI spec and mocking API responses until the backend deploys. |

---

## 5. End-to-End System Flow

```
[Widow / Helper] ---> [Gulab: Next.js PWA on Vercel]
                             │ (HTTPS / JWT / Offline Queue)
                             ▼
                  [Mahandar: FastAPI on AWS EC2]
                  ├── Rate Limiter & Security Guard (JWT, RBAC)
                  ├── Consent Gateway (Audit Log & Permission Check)
                  ├── Rules Engine (Versioned JSON Rules)
                  ├── Decision Engine (Cost Matrix & Threshold Router)
                  └── Mock Services (NADRA, Raast with Chaos Switches)
                             │
                             ├──────────────────────────┐
                             ▼                          ▼
                  [Naresh: AI Services]      [Naresh: Supabase DB]
                  ├── LiteLLM Fallback Chain ├── Postgres Tables
                  ├── OCR & Tamper Detection ├── pgvector Policy Store
                  ├── Whisper STT / edge-TTS ├── Audit Log (Hash-Chained)
                  ├── Scikit-Learn Scam Model└── LangGraph Checkpoints
                  └── LangGraph Agent
```

### 12-Step Demo Path
1. **Helper Mode:** Helper logs in on a shared Android phone, opens Helper Mode, and selects a family from photo cards.
2. **Consent First:** Citizen sees Urdu voice and icon cards (*share identity*, *share income*, *helper acting*). Each toggle writes an audit log entry. No citizen data is read before consent.
3. **Urdu Voice Intake:** Widow speaks in conversational Urdu. Whisper transcribes, and Naresh's Pydantic model extracts structured fields (`name`, `cnic`, `household_size`, `income_band`, `phone`).
4. **Document Upload & Resilience:** Citizen snaps photos of CNIC and electric bill. If network drops, IndexedDB queues upload and resumes upon reconnect.
5. **OCR & Authenticity:** Tesseract extracts Urdu/English text with per-field confidence; blur gate calculates Laplacian variance; QR code is verified; tamper scoring flags digital manipulations.
6. **Identity Resolution:** Matches citizen against mock NADRA using fuzzy name normalization (Urdu transliteration, variant dictionary, RapidFuzz) and exact CNIC matching.
7. **Scam Check (Shopkeeper flow):** Shopkeeper pastes an SMS/WhatsApp message; calibrated classifier outputs `scam`, `legit`, or `unsure` with explainable trigger tags.
8. **Rules Evaluation:** Mahandar's rules engine evaluates the claim against the active versioned rule set and outputs an evaluation trace.
9. **Decision Engine Routing:** Combines all component confidences into weakest-link score ($\text{overall} = \min(\text{components})$):
   * **Auto-Approve:** $p_{\text{wrong}} \le 0.05$, claim amount under threshold, no flags.
   * **Ask for More Proof:** $0.05 < p_{\text{wrong}} \le 0.30$, specifies exact missing or blurry document in Urdu voice/icon.
   * **Hand to Human Officer:** $p_{\text{wrong}} > 0.30$ or conflicting data. A comprehensive handoff packet is attached.
10. **Officer Review:** Department officer reviews queue sorted by priority and confidence, inspects handoff packet, and approves or rejects with a mandatory written reason.
11. **Gated Payout:** Gated tool call triggers mock Raast service only if valid approval token exists in case state.
12. **Notification & Audit:** Citizen receives in-app update and mock SMS; full cryptographic hash-chain record is sealed.

---

## 6. Technical Specifications & Contract

### Agreed Shared Interface (`services/shared/schemas.py`)

To prevent Mahandar and Naresh from blocking each other or causing Git conflicts, `services/shared/schemas.py` is frozen early.

```python
# services/shared/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class RouteDecision(str, Enum):
    AUTO_APPROVE = "auto_approve"
    ASK_MORE_PROOF = "ask_more_proof"
    HUMAN_REVIEW = "human_review"

class ComponentScores(BaseModel):
    identity: float = Field(..., ge=0.0, le=1.0)
    ocr: float = Field(..., ge=0.0, le=1.0)
    authenticity: float = Field(..., ge=0.0, le=1.0)
    rules_complete: float = Field(..., ge=0.0, le=1.0)
    scam_safety: float = Field(..., ge=0.0, le=1.0)

class ReasonSimple(BaseModel):
    en: str
    ur: str

class DecisionResponse(BaseModel):
    case_id: str
    route: RouteDecision
    confidence: float = Field(..., ge=0.0, le=1.0)
    components: ComponentScores
    missing: List[str] = Field(default_factory=list)
    reason_simple: ReasonSimple
    rule_version: int

class ErrorResponse(BaseModel):
    code: str
    message_en: str
    message_ur: str
```

### The 6 AI Functions Naresh Exposes to the API (`services/ai`)

Mahandar imports these directly from `services/ai` without needing to know internal AI implementation details:

1. `extract_documents(files: List[bytes]) -> Dict[str, Any]`  
   *Returns:* Extracted fields with confidence scores, `blur_score`, and `tamper_score`.
2. `classify_message(text: str) -> Dict[str, Any]`  
   *Returns:* `label` (`scam` | `legit` | `unsure`), calibrated `confidence`, and list of `reasons`.
3. `transcribe(audio_bytes: bytes) -> Dict[str, Any]`  
   *Returns:* `text`, detected `language`, and `confidence`.
4. `synthesize(text: str, lang: str = "ur") -> bytes`  
   *Returns:* MP3 audio bytes (cached by MD5 hash of text).
5. `ask_policy(question: str) -> Dict[str, Any]`  
   *Returns:* Markdown formatted `answer` with exact `sources` (policy document name and page number).
6. `run_claim_agent(case_id: str) -> Dict[str, Any]`  
   *Returns:* Execution trace of steps taken and final proposed state.

---

## 7. Concrete Task Cards & Ownership

### Mahandar: Backend, Platform & AWS Infrastructure
* **M1 — Repo & CI Setup:** Initialize repo layout, branch protection, Ruff linter, Pytest workflow, and `.env.example`.
* **M2 — AWS Environment Provisioning:** Launch EC2 (Ubuntu `t3.small`), configure security groups (22, 80, 443), install Docker & Docker Compose, and set up an AWS Budget Alert immediately.
* **M3 — Domain & Automatic HTTPS:** Configure DuckDNS subdomain, set up Caddy reverse proxy for automatic SSL, and verify `/health` over HTTPS on mobile.
* **M4 — OpenAPI Spec Publishing:** Provide initial FastAPI route skeleton and export OpenAPI JSON so Gulab can generate TypeScript client in Block 0.
* **M5 — Authentication & RBAC:** Implement short-lived JWT access tokens + refresh tokens, Argon2 password hashing, and server-side RBAC middleware ensuring citizens receive HTTP 403 on officer endpoints.
* **M6 — Rate Limiting & Safety:** Set up `slowapi` rate limits per IP and API key to protect free-tier LLM limits.
* **M7 — Mock Services with Chaos Mode:** Build `/mock/identity/verify`, `/mock/payment/disburse`, and `/mock/complaints` supporting `?chaos=timeout|500|slow` query params.
* **M8 — Case Management & Review Queue:** Endpoints for case CRUD, document uploads, and officer review queue sorted by priority and confidence.
* **M9 — Versioned Rules Engine:** Immutable rule versioning stored in Supabase; rules evaluation returns condition firing trace without code deployment.
* **M10 — Decision Engine:** Evaluates minimum component confidence, applies cost matrix thresholds, and routes cases.
* **M11 — Consent Gateway & Cryptographic Audit Log:** Enforces `gateway.read(actor, citizen, scope)`; writes hash-chained audit log with PostgreSQL triggers preventing UPDATE and DELETE.
* **M12 — Dual-View Explanation Builder:** Constructs simple citizen explanations (Urdu/English) and detailed auditor traces from rule outputs.
* **M13 (Bonus) — Digital Twin Endpoint & Webhooks:** Endpoint to replay historical cases through draft rule versions and webhook notifications.

---

### Naresh: Agents, AI & Supabase Data Platform
* **N1 — Supabase & Database Provisioning:** Provision Supabase Postgres instance, enable `pgvector` extension, configure connection pooling, and create a keep-alive ping script.
* **N2 — Database Models & Alembic Migrations (`db/`):** Create SQLAlchemy models and Alembic migrations for `users`, `citizens`, `consents`, `cases`, `documents`, `decisions`, `rule_versions`, `review_items`, `audit_log`, `scam_messages`, `eval_results`, and `policy_chunks`.
* **N3 — Synthetic Seed Data Generator (`seed/`):** Script `seed/run_seed.py` that populates Supabase in one command:
  * 200 mock citizens (with name variants like Muhammad/Mohd, 15 duplicate pairs, 30 missing fields, 10 CNIC typos).
  * 200+ labelled SMS/WhatsApp messages (Urdu, Roman Urdu, English) for scam classification.
  * Mock CNIC and utility bill sample images (clean, blurry, tampered).
  * 5–8 mock government policy documents.
* **N4 — Multi-Tier LiteLLM Router (`services/ai/router.py`):** Resilient model router: Groq (Llama-3-70B) $\to$ Gemini $\to$ OpenRouter free $\to$ AWS Bedrock fallback with health checks and response caching.
* **N5 — Scam & Message Classifier (`services/ai/scam.py`):** CPU-trained scikit-learn TF-IDF + Logistic Regression model, calibrated with Platt scaling, returning `scam`/`legit`/`unsure` and explainable rule features.
* **N6 — Document OCR & Authenticity Pipeline (`services/ai/ocr.py`):** Tesseract OCR (`urd+eng`), Laplacian blur gate score, `pyzbar` QR decode against registry, and error-level tamper check.
* **N7 — Urdu Voice Pipeline (`services/ai/voice.py`):** Whisper large-v3 via Groq for STT + `edge-tts` for Urdu speech synthesis with audio caching.
* **N8 — Structured Form Extraction (`services/ai/forms.py`):** Pydantic-based extraction converting messy conversational Urdu text into validated citizen claim fields.
* **N9 — Policy RAG System (`services/ai/rag.py`):** Document chunking, vector embeddings stored in Supabase `pgvector`, and similarity search with citations.
* **N10 — Claim Pipeline & LangGraph Agent (`services/ai/pipeline.py`):** Build deterministic Python pipeline first, then wrap into LangGraph agent with Postgres checkpointing and gated disbursement tool.
* **N11 — Name Normalization & Fuzzy Matcher (`services/ai/matcher.py`):** Transliteration dictionary + RapidFuzz token-set & Jaro-Winkler matching on CNIC first, resolving name variations without incorrect mergers.
* **N12 — Evaluation Harness & Threshold Sweep (`services/ai/eval.py`):** Computes precision, recall, false-alarm rates, and cost-curve sweep, writing results directly to `eval_results` for Gulab's UI dashboard.
* **N13 (Bonus) — Anomaly Detection:** `IsolationForest` model on claim features to detect duplicate assistance patterns.

---

### Gulab: Frontend & Mobile PWA (`apps/web/`)
* **G1 — Next.js PWA Foundation:** Setup Tailwind CSS, shadcn/ui components, Urdu RTL font (`Noto Nastaliq Urdu`), and large touch targets for low-literacy users.
* **G2 — Typed API Client:** Generate TypeScript SDK from Mahandar's OpenAPI spec; build MSW mock fixtures for local UI development.
* **G3 — Role-Based Shell:** Dynamic navigation menu displaying views according to JWT role (Citizen, Helper, Officer, Admin, Auditor).
* **G4 — Voice-First Citizen Flow:** Step-by-step UI with large icon buttons, one question per screen, and audio play buttons.
* **G5 — Helper Mode Switcher:** Quick switcher allowing community helpers to switch between 40 family profiles with 2 taps.
* **G6 — Consent Management & "Who Has My Data":** Visual consent cards with audio explanations and one-tap withdrawal.
* **G7 — Case Tracker & Officer Review Queue:** Visual status tracking for citizens; triage table for officers sorted by priority and confidence with full handoff packet view.
* **G8 — Admin Rule Editor & Digital Twin UI:** Interactive condition builder for eligibility rules and simulation diff view before publishing.
* **G9 — Auditor & Observability Dashboard:** Read-only inspection views for hash-chained audit logs, AI confidence traces, and decisions.
* **G10 — Scam Checker & Evaluation Dashboard:** Shopkeeper SMS analyzer view and interactive chart rendering Naresh's threshold sweep data.
* **G11 — Offline Queue & Low-Bandwidth Mode:** Service worker and IndexedDB queue storing forms and uploads locally when offline, syncing automatically on reconnect.
* **G12 — Presentation & Video Assets:** Final Vercel deployment, demo video recording, presentation slides, and README screenshots.

---

## 8. Git Workflow: Independent & Conflict-Free

To ensure smooth pull requests and zero merge collisions:

1. **Branch Naming by Domain:**
   * Infrastructure / AWS / Backend: `feat/api-<feature>` or `feat/infra-<feature>` (Mahandar)
   * Database / Seed / AI: `feat/db-<feature>` or `feat/ai-<feature>` (Naresh)
   * Frontend: `feat/web-<feature>` (Gulab)
2. **Directory Isolation:** No team member edits files in another person's directory without prior coordination.
   * Mahandar: `services/api/`, `mock/`, `infra/`, `.github/`
   * Naresh: `services/ai/`, `db/`, `seed/`
   * Gulab: `apps/web/`
   * Shared: `services/shared/schemas.py` is locked after initial agreement.
3. **Database Migrations Protocol:** Naresh writes and tests Alembic migrations in `db/`. When merged to `main`, Mahandar's deploy script runs `alembic upgrade head` automatically.
4. **Pull Requests:** Keep PRs under 300 lines. Another team member reviews and approves before merging into `main`. CI must pass (Ruff + Pytest + Web build) before any merge.

---

## 9. 28-Hour Hackathon Timeline

| Block | Window | Focus Area | Exit Gate Check |
| :--- | :--- | :--- | :--- |
| **0. Contract** | T+0 to T+3 | Repo setup, AWS EC2 hello-world (Mahandar), Supabase provisioning + Alembic schema (Naresh), OpenAPI spec export, Web fixtures (Gulab). | Gulab calls mock API from Next.js; AWS `/health` endpoint responds with 200 OK. |
| **1. Foundations** | T+3 to T+9 | Auth & RBAC (Mahandar), Seed data generation & LiteLLM router (Naresh), Citizen flow UI skeleton (Gulab). | Test user logs in; seed data populates Supabase with 1 command; scam model trains. |
| **Rest** | T+9 to T+14 | **Mandatory sleep block.** Rested teams deliver working demos without panic. | N/A |
| **2. Intelligence** | T+14 to T+19 | Rules engine & Decision router (Mahandar), Voice STT/TTS & OCR & LangGraph agent (Naresh), Helper Mode & Officer queue UI (Gulab). | Full end-to-end happy path executes successfully on local environment. |
| **3. Trust & Safety** | T+19 to T+23 | Consent gateway & Audit hash chain (Mahandar), RAG policy search & Eval sweep script (Naresh), Digital Twin & Eval UI (Gulab). | All 8 hackathon challenges have visible, interactive demo screens. |
| **4. Deployment** | T+23 to T+26 | EC2 Caddy HTTPS deployment (Mahandar), Supabase keep-alive ping verification (Naresh), Vercel production deploy (Gulab). | Live URL works smoothly on a throttled mobile phone connection. |
| **5. Freeze & Polish**| T+26 to T+28 | **Feature freeze.** Bug fixes only. Demo video recording, presentation slides, README documentation, submission form. | Submission checklist verified 100% complete. |

---

## 10. Demo Script (7-Minute Presentation)

1. **Problem & Three Personas (30s):** The widow who cannot read, the shopkeeper targeted by scam texts, and the helper managing 40 families on one shared phone.
2. **Helper Mode & Granular Consent (90s):** Two-tap family switch. Citizen sees Urdu icon/voice consent card. Citizen grants identity & income consent. Consent record is logged.
3. **Voice Intake & Offline Resilience (60s):** Widow speaks in Urdu; Whisper transcribes; Pydantic extracts fields. Photos taken; simulate network disconnect; upload resumes seamlessly.
4. **Three Cases Through Decision Engine (90s):**
   * *Case A (Clean):* Auto-approves under threshold.
   * *Case B (Blurry doc):* Asks for specific missing document in Urdu voice.
   * *Case C (Conflicting info):* Routes to officer review queue with full handoff packet.
5. **Officer Review & Gated Disbursement (45s):** Officer inspects handoff packet and approves. Gated tool executes mock Raast payment.
6. **Admin Rule Editor & Digital Twin (60s):** Admin updates income threshold; Digital Twin replays historical cases to visualize impact before publishing. New decision uses new rule with no server restart.
7. **Consent Withdrawal & Audit Integrity (60s):** Citizen withdraws consent; subsequent read request is immediately blocked (HTTP 403) and logged. Auditor inspects hash-chained tamper-evident log.
8. **Scam Detection & Eval Metrics (45s):** Shopkeeper pastes fake relief SMS and receives immediate scam warning. View evaluation dashboard showing real threshold sweep curves.
9. **Real vs. Simulated & Wrap-Up (30s):** Summary of architecture, real AI models vs simulated national rails, and impact.
