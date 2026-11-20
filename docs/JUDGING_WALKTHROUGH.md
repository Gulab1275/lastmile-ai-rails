# Rahbar (رہبر) — Official Judging & Evaluation Walkthrough
**Event:** Coder's Cup '26 · AI Hackathon · FAST-NUCES Karachi  
**Team:** Mahandar Khatri (Backend & AWS) · Naresh Kumar (AI & Supabase) · Gulab (Frontend & PWA)

---

## 1. Executive Summary & One Sentence
> **We help a community helper (and the widows and shopkeepers she serves) apply for a mock Relief Cash Support claim, even though they cannot read the forms, have a weak connection, and keep receiving fake relief messages.**

Every DPI system, payment rail, identity ladder, and ML model can be verified live in under 2 minutes:
- **FastAPI Backend Server:** `uvicorn services.api.main:app --port 8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Automated Test Suite:** `python -m pytest tests/ -v` (**37 / 37 passed**)
- **12-Step Presentation Runner:** `python scripts/demo_runner.py` (**100% verified**)
- **Supabase Keep-Alive:** `python scripts/keepalive_ping.py`

---

## 2. Hackathon Challenges Matrix (All 8 Addressed)

| Challenge | Real Implementation | Where in Code | Live Verification Step |
| :--- | :--- | :--- | :--- |
| **01: Cost of Being Wrong** | Weakest-link rule $\min(\text{components})$; auto-approve strictly requires $p_{\text{wrong}} \le 0.05$. | `services/api/engine/decision_engine.py`<br/>`services/ai/eval.py` | Run `python -m pytest tests/test_decision_engine.py` |
| **02: Saying "I Am Not Sure"** | Low confidence routes to Human Officer queue with handoff notes; **Never Auto-Rejects**. | `services/api/routes/review.py`<br/>`services/ai/pipeline.py` | Review queue: `GET /api/v1/review/queue` |
| **03: Bad Data Handling** | Fuzzy name normalization with Urdu transliteration dictionary + RapidFuzz matching on CNIC first. | `services/ai/matcher.py`<br/>`seed/run_seed.py` | Test with Muhammad vs Mohammad; no false mergers. |
| **04: Rules That Change** | Dynamic JSON rules stored in Supabase; new rules take effect instantly without code deploy. | `services/api/engine/rules_engine.py`<br/>`services/api/routes/rules.py` | Publish via `POST /api/v1/rules/publish` |
| **05: Explain and Audit** | Dual-view explainability (plain Urdu voice for citizens, parameters for auditors) + SHA-256 hash-chained ledger. | `services/api/engine/explanation_builder.py`<br/>`services/api/engine/audit_log.py` | Verify chain: `GET /api/v1/audit/verify-chain` |
| **06: Consent & Take-Back** | Server-side Consent Gateway enforces granular scopes; revocation immediately blocks reads (HTTP 403). | `services/api/engine/consent_gateway.py`<br/>`services/api/routes/consent.py` | Withdraw scope via `POST /api/v1/consent/withdraw` |
| **07: Works for Everyone** | Voice-first conversational Urdu intake, Edge-TTS speech synthesis, and offline-first sync. | `services/ai/voice.py`<br/>`services/ai/forms.py`<br/>`services/ai/sync.py` | Run `POST /api/v1/ai/voice/tts` and `POST /api/v1/ai/extract-form` |
| **08: Scams & Fake Documents** | Scikit-learn calibrated classifier for relief SMS; Laplacian blur gate (<90) and ELA tamper detection. | `services/ai/scam.py`<br/>`services/ai/ocr.py`<br/>`services/ai/scam_map.py` | Run `POST /api/v1/ai/scam-check` and `GET /api/v1/ai/scam-map` |

---

## 3. Creative Bonus Features (All 4 Delivered)

1. **Digital Twin (`/api/v1/digital-twin/simulate`):**
   - Allows administrators to simulate draft rule impact on a corpus of historical cases before publishing live.
   - Calculates baseline vs projected approval rates, fiscal impact, and affected citizen counts.

2. **Scam Map & Geo-Threat Heatmap (`/api/v1/ai/scam-map`):**
   - Clusters classified phishing reports into GPS hotspots across Karachi (Saddar, Liaquatabad, Gulshan, Orangi, Malir, Korangi) and Sindh.
   - Categorizes attack vectors (`fake_disbursement`, `pin_harvesting`, `registration_fee`, `lottery_scam`) and tracks top trigger phrases.

3. **Task N13 Machine Learning Anomaly Detection (`/api/v1/ai/anomaly-check`):**
   - Scikit-learn `IsolationForest` model combined with heuristic rules.
   - Detects helper velocity bursts (> 15 claims/24h), repeat CNIC/phone combinations, and income-to-request ratio outliers.

4. **Offline-First Synchronization Protocol (`/api/v1/ai/sync-offline-batch`):**
   - Supports helpers working in zero-signal areas.
   - Queues claims and audio locally; upon reconnect, syncs with guaranteed **idempotency deduplication** (duplicate submissions return cached receipts without re-triggering payouts).

---

## 4. Pre-Seeded Demo Logins (5 Roles)

| Role | Username | Password | Persona & Key Action |
| :--- | :--- | :--- | :--- |
| **Citizen (Widow)** | `citizen_parveen` | `password123` | Speaks Urdu, applies for relief, toggles data consent. |
| **Citizen (Shopkeeper)**| `citizen_tariq` | `password123` | Pastes phishing SMS, receives instant calibrated scam warning. |
| **Community Helper** | `helper_shazia` | `password123` | Manages 40 family profiles on a shared phone with separate consent. |
| **Department Officer** | `officer_aslam` | `password123` | Reviews escalated cases sorted by priority; approves/rejects with notes. |
| **System Admin** | `admin_ayesha` | `password123` | Simulates rule changes in Digital Twin and publishes dynamically. |
| **Compliance Auditor** | `auditor_iqbal` | `password123` | Inspects tamper-evident SHA-256 blockchain audit trail. |

---

## 5. Live Command Walkthrough

```bash
# 1. Run the entire automated test suite (37 tests, 100% passing)
python -m pytest tests/ -v

# 2. Run the 12-Step Hackathon Presentation Script
python scripts/demo_runner.py

# 3. Verify Supabase Database Heartbeat & Pool
python scripts/keepalive_ping.py

# 4. Start API Gateway
uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```
Interactive Swagger API documentation: `http://localhost:8000/docs`
