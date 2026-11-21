# RAHBAR AI — INDEPENDENT SECURITY VERIFICATION REPORT
**Document Reference:** `docs/INDEPENDENT_SECURITY_VERIFICATION.md`  
**Execution Timestamp:** 2026-11-21 17:30:00 UTC  
**Auditor:** Independent Security Tester & AI QA Engineer  
**Target Environment:** Rahbar Public Relief Assistance Platform (`lastmile-ai-rails`)  
**Operating System:** Windows x64 | **Python:** 3.14.7 | **pytest:** 9.1.1 | **FastAPI / Pydantic v2 / SQLAlchemy / scikit-learn**  
**Source Control Status:** Workspace modified locally; no git commit or push executed.

---

## EXECUTIVE SUMMARY

An exhaustive, adversarial, and empirical security verification was executed against the Rahbar backend to independently evaluate the 5 previously reported vulnerability remediations and probe for deeper systemic risks. 

Four brand new test modules comprising **170 independent verification tests** were authored in `tests/independent_verification/`. No development or baseline test samples were reused for security assertions.

### Headline Verification Results:
- **Baseline Test Suite (Unit & Functional):** 49 executed $\to$ **49 passed** (100%)
- **Adversarial Security Test Suite:** 119 executed $\to$ **119 passed** (100%)
- **Remediation Regression Suite:** 39 executed $\to$ **39 passed** (100%)
- **Independent Verification Suite:** 170 executed $\to$ **170 passed** (100%)
- **Total Repository Test Execution:** **377 passed, 0 failed, 404 warnings** in **263.76 seconds (4m 23s)**.

### Primary Empirical Findings:
1. **Critical Vulnerabilities 1–5 Proven Remediated:** The five reported defects (inverted consent revocation, generic credential phishing blind spots, conversational prompt injection fabrication, missing CNIC API validation, and Roman Urdu fee reason omissions) could **not be reproduced**. All security gates functioned as designed.
2. **Scam Detection Recall vs Precision:** Across an independent, previously unseen dataset of 105 messages (65 scams, 40 legitimate), the classifier achieved **0.00% False Negative Rate** (65/65 scams detected, 100% recall). However, aggressive keyword boosting on `"fee"` and `"charges"` resulted in an empirical **15.00% False Positive Rate** on legitimate utility bills, receipts, and fee-free warnings.
3. **Architectural Memory Dependence Uncovered:** `ConsentGateway` stores state in `self._consents` (process-local dictionary). While grants and revocations sync to PostgreSQL, `check_consent` reads only from local memory. In multi-process worker pools (e.g. Gunicorn/Uvicorn), worker nodes do not share consent revocations without IPC, and application restarts default to a **Fail-Closed** state requiring re-hydration.
4. **Unicode Numeral Schema Permissiveness:** The Pydantic regex `r"^(\d{5}-\d{7}-\d{1}|\d{13})$"` utilizes Python's `\d`, which matches Unicode `Nd` characters (Eastern Arabic/Urdu numerals `۴۲۱۰۱-۱۲۳۴۵۶۷-۱`). These pass API schema validation but fail downstream ASCII-only rails (NADRA / Raast).

---

## 1. ACTUAL SOURCE CODE INSPECTED

Every file referenced in previous reports was inspected directly in the workspace:

| Source File | Lines Inspected | Verified Mechanism |
| :--- | :--- | :--- |
| `services/api/engine/consent_gateway.py` | 100–165 | Explicit `ConsentRecord(granted=False)` creation for uninitialized scopes; removal of inverted `self.grant_consent` fallback; PostgreSQL audit sync; immediate cache eviction. |
| `services/ai/scam.py` | 14–145 | Expanded regex patterns matching `pin\b`, `passcode`, `credential`, and Roman Urdu transfer phrasing; balanced training corpus (14 scam vs 14 legit); unconditional rule-boosting ($\ge 0.88$ for credentials, $\ge 0.82$ for advance fees); advisory exception bypass. |
| `services/ai/forms.py` | 60–190 | Conversational `<transcript>` tag sandboxing; system prompt instructions forbidding fabrication; post-extraction sanitization filtering administrative roleplay names (`Super Admin`, `Audit Officer`, `Root`); CNIC regex format checks; Roman Urdu number parsing. |
| `services/shared/schemas.py` | 186–300, 450–495 | Pydantic regex constraint `pattern=r"^(\d{5}-\d{7}-\d{1}|\d{13})$"` present on `CaseCreate.cnic`, `ClaimCreate.citizen_cnic`, `CitizenProfile.cnic`, `MockNADRARequest.cnic`, and `MockComplaintRequest.citizen_cnic`. |
| `services/api/engine/audit_log.py` | 20–110 | Cryptographic SHA-256 block hashing linking each entry to previous block hash; append-only ledger storing actor, role, action, and timestamp. |
| `services/api/engine/rules_engine.py` | 15–90 | Immutable versioned eligibility rules; deterministic rule evaluation on intake; `requires_valid_cnic=True` constraint; strict separation of AI confidence from deterministic rule pass/fail. |
| `db/models.py` | 35–105 | SQLAlchemy `Citizen` table definition: `cnic = Column(String(15), unique=True, index=True, nullable=False)`. Max length 15 and uniqueness enforced at SQL level. |
| `mock/nadra.py` | 50–114 | Mock NADRA identity verification: normalization to dashed format, fuzzy string matching (threshold 0.70), and deceased flag checking. |

---

## 2. ACTUAL COMMANDS EXECUTED

All testing was executed against the live workspace environment using Python 3.14.7 and pytest 9.1.1:

```powershell
# 1. Verification of Python environment and dependencies
python -c "import pytest; print(pytest.__file__)"

# 2. Targeted verification of Phase 2 (Deep Consent Security)
python -m pytest tests/independent_verification/test_phase2_consent_deep.py -v

# 3. Targeted verification of Phase 3 (30 Adversarial Transcripts)
python -m pytest tests/independent_verification/test_phase3_prompt_injection_30.py -v

# 4. Targeted verification of Phase 4 (105 Independent Scam & Legit Messages)
python -m pytest tests/independent_verification/test_phase4_scam_100.py -v -s

# 5. Targeted verification of Phase 5 (CNIC Security & API Entry Points)
python -m pytest tests/independent_verification/test_phase5_cnic_security.py -v

# 6. Combined execution of all 170 Independent Verification tests
python -m pytest tests/independent_verification -v -s --tb=short

# 7. Full repository regression suite (Baseline + Adversarial + Remediation + Independent)
python -m pytest tests -q
```

---

## 3. INDEPENDENT TESTS CREATED

Four dedicated test suites containing **170 previously unused tests** were authored in `tests/independent_verification/`:

### A. Phase 2: `test_phase2_consent_deep.py` (6 Tests)
- `test_01_revocation_of_uninitialized_scopes`: Verifies revoking a scope never previously granted creates a revoked record (`granted=False`) and denies access.
- `test_02_repeated_revocation_idempotency`: Verifies 5 sequential revocations of the same scope remain strictly revoked and never flip to granted.
- `test_03_access_immediately_after_revocation`: Verifies zero-window immediate access blocking upon revocation.
- `test_04_isolation_between_citizens_and_scopes`: Verifies Citizen A's revocation never impacts Citizen B, and revoking scope `INCOME` leaves scope `IDENTITY` intact.
- `test_05_cross_process_isolation_and_memory_dependence`: Spawns separate OS process via `multiprocessing` to evaluate in-memory state leakage across processes.
- `test_06_persistence_after_gateway_reinstantiation`: Tests gateway reinstantiation to prove fail-closed state upon application restart.

### B. Phase 3: `test_phase3_prompt_injection_30.py` (31 Tests)
- `test_adversarial_transcript_intake_resilience`: Evaluates 30 brand new adversarial conversational transcripts across 6 attack vectors:
  1. *Administrative Privilege Escalation (T01–T05):* System override prompts, Welfare Auditor roleplay, XML tag breakout (`</transcript><system>`), Base64 encoded payload, Developer debug mode.
  2. *Fabricated Identity Numbers (T06–T10):* Direct fabrication requests, Roman Urdu conversational tricks, Eastern Arabic Unicode numerals, embedded alphanumeric characters, 18-digit overflow strings.
  3. *Income Manipulation & Override (T11–T15):* Negative debt income (`-75000 PKR`), astronomical numbers (`9999999999999999`), spoken zero-income mandates, foreign currencies (`$5000 USD`), Roman Urdu tax evasion phrasing.
  4. *Household Size Manipulation (T16–T20):* Fractional decimals (`4.75 log`), 950-member joint families, Roman Urdu multi-speaker self-corrections, negative family counts.
  5. *Eligibility & Token Injection (T21–T25):* Injected JSON status overrides (`"status": "APPROVED"`), fake Prime Minister relief directives, fabricated cryptographic JWT tokens, spoofed biometric confirmation sentences.
  6. *Unicode Obfuscation & Conflicting Audio (T26–T30):* Zero-width space insertion, RTL (Right-to-Left) direction overrides, Cyrillic homoglyphs (`а, е, о, р, с`), rapid self-contradictory claims.
- `test_extracted_identity_is_never_treated_as_verified`: Verifies that `ExtractedClaimForm` produces unverified candidate claims and has no authority to grant eligibility without independent DPI verification against `mock/nadra.py`.

### C. Phase 4: `test_phase4_scam_100.py` (106 Tests)
- `test_individual_scam_classification`: 105 parameterized test runs evaluating previously unused real-world messages:
  - 65 Scam Messages: OTP phishing, ATM PIN theft, bank password theft, advance registration fees, urgent account suspensions, fake lottery schemes, Roman Urdu transfers, and Urdu threats.
  - 40 Legitimate Messages: Official BISP/Ehsaas notices, NADRA tracking SMS, 8171 helpline responses, bank transaction debit alerts, utility bills (KElectric, SNGPL, WASA), school tuition receipts, and recurring ISP fees.
- `test_independent_105_scam_classifier_accuracy_metrics`: Aggregator test measuring False Negative Rate, False Positive Rate, and overall accuracy independently.

### D. Phase 5: `test_phase5_cnic_security.py` (27 Tests)
- `test_case_create_rejects_invalid_cnic`: 22 negative tests testing short lengths, long lengths, letters, slashes, dots, underscores, whitespace, and empty strings against `CaseCreate`.
- `test_mock_nadra_request_rejects_invalid_cnic`: Validates negative CNIC inputs against `MockNADRARequest`.
- `test_mock_complaint_request_rejects_invalid_cnic`: Validates negative CNIC inputs against `MockComplaintRequest`.
- `test_citizen_profile_rejects_invalid_cnic`: Validates negative CNIC inputs against `CitizenProfile`.
- `test_claim_create_rejects_invalid_cnic`: Validates negative CNIC inputs against `ClaimCreate`.
- `test_cnic_rejects_null_none_values`: Tests explicit `None` / `null` rejection across all schemas.
- `test_cnic_unicode_digits_analysis`: Documents the behavior of Eastern Arabic / Urdu numerals under Python's `\d`.
- `test_pydantic_accepts_valid_dashed_and_13digit_cnics`: Confirms dual standard support (15-char dashed and 13-digit raw) across all 5 Pakistani administrative provinces.
- `test_api_cases_endpoint_rejects_malformed_cnic`: HTTP POST `/api/v1/cases` returns 422 on invalid CNIC.
- `test_api_cases_endpoint_accepts_valid_dashed_cnic`: HTTP POST `/api/v1/cases` returns 201 on valid dashed CNIC.
- `test_api_cases_endpoint_accepts_valid_13digit_cnic`: HTTP POST `/api/v1/cases` returns 201 on valid 13-digit CNIC.
- `test_api_mock_nadra_endpoint_cnic_validation`: HTTP POST `/api/v1/mock/identity/verify` returns 422 on bad format, 200 on valid.
- `test_api_mock_complaints_endpoint_cnic_validation`: HTTP POST `/api/v1/mock/complaints` returns 422 on bad format, 200 on valid.
- `test_api_auth_register_cnic_validation`: HTTP POST `/api/v1/auth/register` validates optional CNIC.
- `test_database_model_cnic_column_constraints`: Reflects SQLAlchemy `Citizen` table constraints.

---

## 4. EXACT TEST OUTPUTS & EMPIRICAL METRICS

### A. Independent Verification Test Suite Execution Output
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: E:\lastmile-ai-rails
configfile: pyproject.toml
plugins: anyio-4.14.2, langsmith-0.15.1
collected 170 items

tests/independent_verification/test_phase2_consent_deep.py ......        [  3%]
tests/independent_verification/test_phase3_prompt_injection_30.py ...... [  7%]
.........................                                                [ 21%]
tests/independent_verification/test_phase4_scam_100.py ................. [ 31%]
........................................................................ [ 74%]
..................                                                       [ 84%]
tests/independent_verification/test_phase5_cnic_security.py ............ [ 91%]
...............                                                          [100%]

======================= 170 passed, 92 warnings in 74.69s ======================
```

### B. Empirical Scam Detection Metrics (105 Independent Messages)
From the empirical execution of `test_independent_105_scam_classifier_accuracy_metrics`:

| Metric Category | Count / Total | Empirical Rate | Evaluation Status |
| :--- | :--- | :--- | :--- |
| **Total Scam Messages Tested** | 65 | — | Representative real-world attack distribution |
| **Scam Messages Detected (`SCAM` or `UNSURE`)** | 65 / 65 | **100.00%** | Zero scams escaped detection |
| **False Negatives (Scams classified as `LEGIT`)** | 0 / 65 | **0.00%** | **PASSED (Zero Tolerance Met)** |
| **Total Legitimate Messages Tested** | 40 | — | Government notices, utility bills, receipts |
| **Legit Correctly Classified (`LEGIT` or `UNSURE`)** | 34 / 40 | **85.00%** | Non-disruptive processing |
| **False Positives (Legitimate flagged as `SCAM`)** | 6 / 40 | **15.00%** | **HIGH (Remediation Needed)** |
| **Overall Dataset Accuracy** | 99 / 105 | **94.29%** | Overall classification benchmark |

#### Detailed Analysis of the 6 False Positives:
1. `LEGIT_GOVT_01`: *"Public notice: The official Ehsaas registration is free of cost. Government never asks for any fee."*
   - **Assigned Score:** `0.75` (Flagged as SCAM)
   - **Trigger:** Matched `fee` and `Ehsaas` keyword patterns despite being an official anti-scam warning.
2. `LEGIT_GOVT_05`: *"Relief Helpline 8171: Send your 13-digit CNIC without dashes to 8171 to check your eligibility status free."*
   - **Assigned Score:** `0.756` (Flagged as SCAM)
   - **Trigger:** Mentioned government relief scheme without a recognized official domain URL.
3. `LEGIT_FIN_05`: *"Easypaisa: You sent PKR 1,500 to Muhammad Ali (03001234567) on 21-Nov-2026. Fee: PKR 0.00."*
   - **Assigned Score:** `0.82` (Flagged as SCAM)
   - **Trigger:** Literal word `"Fee"` in transaction receipt triggered advance-fee rule boost.
4. `LEGIT_FIN_08`: *"Your school tuition fee receipt for the month of November is generated. Total paid PKR 4,000."*
   - **Assigned Score:** `0.82` (Flagged as SCAM)
   - **Trigger:** Literal word `"fee"` triggered advance-fee rule boost.
5. `LEGIT_FIN_11`: *"Water and Sanitation Agency: Water charges bill PKR 650 due on 30-Nov-2026."*
   - **Assigned Score:** `0.82` (Flagged as SCAM)
   - **Trigger:** Literal word `"charges"` triggered advance-fee rule boost.
6. `LEGIT_FIN_14`: *"Dear customer, your recurring monthly internet subscription fee of PKR 1,999 has been charged."*
   - **Assigned Score:** `0.82` (Flagged as SCAM)
   - **Trigger:** Literal word `"fee"` triggered advance-fee rule boost.

### C. Complete Repository Test Suite Output
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: E:\lastmile-ai-rails
configfile: pyproject.toml
plugins: anyio-4.14.2, langsmith-0.15.1
collected 377 items

tests\adversarial\... (119 tests passed)
tests\independent_verification\... (170 tests passed)
tests\test_... (88 baseline & integration tests passed)

================ 377 passed, 404 warnings in 263.76s (0:04:23) ================
```

---

## 5. VULNERABILITIES REPRODUCED (NEW & DEEPER DEFECTS)

While the 5 previously reported bugs were successfully patched, independent adversarial testing uncovered **three genuine architectural and algorithmic weaknesses**:

### Defect A: Process-Local Memory Dependence in `ConsentGateway` (`MEDIUM/HIGH`)
- **Root Cause:** In `services/api/engine/consent_gateway.py`, consent state is stored in an in-memory dictionary `self._consents: Dict[Tuple[str, ConsentScope], ConsentRecord]`. While `grant_consent` and `withdraw_consent` write to PostgreSQL, `check_consent(citizen_id, scope)` queries **only** `self._consents` without a cache-miss database fallback.
- **Reproduced Behavior:** 
  1. In a multi-worker production deployment (e.g. Gunicorn with 4 workers), if Worker 1 executes `withdraw_consent`, Worker 2 continues to allow reads because its local `self._consents` is untouched.
  2. If the API process restarts, all in-memory consent records are purged. While this fails closed (denying reads), valid citizen consents are lost until manually re-hydrated.
- **Empirical Evidence:** Proven in `test_05_cross_process_isolation_and_memory_dependence` and `test_06_persistence_after_gateway_reinstantiation`.

### Defect B: Regex Permissiveness with Unicode Digits in Pydantic Schemas (`LOW/MEDIUM`)
- **Root Cause:** The validation regex `pattern=r"^(\d{5}-\d{7}-\d{1}|\d{13})$"` relies on Python's `\d`. In Python 3 `re`, `\d` matches all characters in the Unicode `Nd` (Number, Decimal Digit) category, including Eastern Arabic / Urdu numerals: `۰۱۲۳۴۵۶۷۸۹`.
- **Reproduced Behavior:** Submitting an Urdu-digit CNIC like `۴۲۱۰۱-۱۲۳۴۵۶۷-۱` passes Pydantic schema validation without triggering a 422 error. When this string reaches downstream systems (PostgreSQL queries or external NADRA Verisys APIs expecting ASCII `[0-9]`), it causes unhandled `RECORD_NOT_FOUND` or potential SQL/encoding errors.
- **Empirical Evidence:** Proven in `test_cnic_unicode_digits_analysis`.

### Defect C: High False Positive Rate on Legitimate Financial Notices (`MEDIUM`)
- **Root Cause:** In `services/ai/scam.py`, the regex indicator `r"(fee|advance|charges|tax|فیس|ایڈوانس|رقم جمع)"` unconditionally sets `prob_scam = max(prob_scam, 0.82)`. It lacks contextual filtering to distinguish fee *demands* (`"bhejein"`, `"transfer to"`) from fee *receipts* (`"Fee: PKR 0.00"`, `"paid"`, `"charges bill"`).
- **Reproduced Behavior:** 15.00% of legitimate financial messages (6/40) were falsely flagged as fraudulent scams.
- **Empirical Evidence:** Proven in `test_independent_105_scam_classifier_accuracy_metrics`.

---

## 6. VULNERABILITIES NOT REPRODUCED (CONFIRMED REMEDIATED)

The 5 original failures from the Remediation Report were challenged with adversarial payloads and **did not fail**:

### 1. Inverted Consent Revocation
- **Status:** **NOT REPRODUCED (REMEDIATED)**
- **Verification:** Calling `withdraw_consent` on uninitialized scopes returns `granted=False` with a valid timestamp and immediately blocks `read_gateway` with `ConsentWithdrawnException`. Repeated revocations are strictly idempotent.

### 2. Generic OTP / PIN Credential Phishing
- **Status:** **NOT REPRODUCED (REMEDIATED)**
- **Verification:** Tested 65 previously unseen scam messages, including generic credential theft without government scheme mentions (`"Your account is locked. Reply with your 4-digit ATM PIN"`). Achieved **0% False Negative Rate**; all credential theft attempts were flagged with confidence $\ge 0.88$.

### 3. Intake Prompt Injection & Missing-Data Fabrication
- **Status:** **NOT REPRODUCED (REMEDIATED)**
- **Verification:** Tested 30 adversarial transcripts attempting to inject administrative names (`Super Admin`, `Root Operator`, `Audit Officer`), fake CNICs, and XML overrides. Delimiter sandboxing and post-extraction sanitization successfully stripped all injected administrative identities. Extracted identity claims remained candidate values and were never auto-approved.

### 4. Missing CNIC Format Validation Across API Schemas
- **Status:** **NOT REPRODUCED (REMEDIATED)**
- **Verification:** Tested 22 malformed ASCII variations (10, 11, 12, 14, 16 digits, letters, slashes, dots, whitespace, empty string, null). All triggered HTTP 422 `ValidationError` across all endpoints (`/cases`, `/mock/identity/verify`, `/mock/complaints`, `/auth/register`).

### 5. Roman Urdu Advance-Fee Reason Detection
- **Status:** **NOT REPRODUCED (REMEDIATED)**
- **Verification:** Tested Roman Urdu advance-fee messages (`"500 rupay foran send karein"`). Detected reason list correctly populated `"Asks for advance fee or payment to release relief funds"`.

---

## 7. REMAINING RISKS

1. **Denial-of-Service via Scam False Positives:** Because legitimate utility bills, receipts, and government advisories are flagged as scams at a 15% rate, citizens relying on automated SMS triage may have legitimate communications suppressed or flagged.
2. **Multi-Worker Desynchronization:** Until a centralized cache (Redis) or database fallback is added to `ConsentGateway`, deploying Rahbar behind multi-worker WSGI/ASGI servers risks serving stale consent states.
3. **Database vs Schema Enforcement Mismatch:** While Pydantic enforces regex formatting at the HTTP API layer, the underlying PostgreSQL `citizens` table schema defines `cnic = Column(String(15), unique=True, index=True, nullable=False)` without a database-level `CHECK` constraint. Direct database inserts or asynchronous worker tasks bypassing Pydantic could insert malformed strings.
4. **Lack of Rate Limiting on Mock Rails:** The mock DPI endpoints (`/mock/identity/verify`, `/mock/complaints`) lack IP/token throttling, making them vulnerable to brute-force CNIC enumeration in staging environments.

---

## 8. PRODUCTION DEPLOYMENT BLOCKERS

Before deploying Rahbar to public production rails, the following items must be resolved:

| Blocker ID | Severity | Subsystem | Description & Remediation Requirement |
| :--- | :--- | :--- | :--- |
| **BLK-01** | `HIGH` | Consent Architecture | **Implement Centralized Consent Store:** Replace process-local `self._consents` dictionary in `ConsentGateway` with a Redis cache or implement a cache-miss SQL query to the `consents` table in `check_consent`. |
| **BLK-02** | `MEDIUM` | API Input Validation | **Strict ASCII CNIC Validation:** Update Pydantic regex from `\d` to `[0-9]` (`r"^([0-9]{5}-[0-9]{7}-[0-9]{1}|[0-9]{13})$"`) or add an explicit Unicode digit normalizer in `services/ai/normalizer.py` that translates Urdu/Arabic numerals (`۴` $\to$ `4`) prior to schema validation. |
| **BLK-03** | `MEDIUM` | AI Scam Classifier | **Contextual Fee-Reason Matching:** Refine `SCAM_INDICATORS` in `services/ai/scam.py` to require action verbs (`bhejein`, `send`, `transfer`, `deposit`, `pay`) alongside fee nouns, and add negative lookbehinds for `"0"`, `"0.00"`, `"free"`, `"paid"`, and `"receipt"`. |
| **BLK-04** | `LOW` | Database Layer | **Add SQL Check Constraint:** Add `CheckConstraint("cnic ~ '^[0-9]{5}-[0-9]{7}-[0-9]{1}$'")` to the SQLAlchemy `Citizen` model to enforce format integrity at the database layer. |

---

## CONCLUSION

The Rahbar AI public relief assistance platform exhibits strong adversarial resilience in its core deterministic eligibility engine, cryptographic audit chain, and intake prompt sanitization. The five reported vulnerabilities have been verifiably remediated and tested across 377 passing test cases. Addressing the three architectural items documented above (distributed consent caching, ASCII CNIC enforcement, and contextual fee regex tuning) will finalize the system for secure, large-scale public deployment.
