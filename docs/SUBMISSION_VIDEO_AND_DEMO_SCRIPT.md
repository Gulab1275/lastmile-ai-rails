# Rahbar (رہبر) — Official Hackathon Video Walkthrough & Presentation Script

> **Coder's Cup '26 — AI-Powered Digital Public Infrastructure Rails for The Last Mile**  
> **Team**: Mahandar Khatri · Naresh Kumar · Gulab  
> **Live Frontend (Vercel)**: [https://lastmile-ai-rails.vercel.app](https://lastmile-ai-rails.vercel.app)  
> **Production API (AWS EC2)**: [https://rahbar-backend.duckdns.org](https://rahbar-backend.duckdns.org)  
> **Target Video Duration**: 3 to 5 Minutes  
> **Target Score**: 100/100 (Full coverage of all 8 Hackathon Challenges & 4 Creative Features)

---

## 1. Video Recording Setup Checklist

- [ ] **Resolution**: 1080p (1920x1080) at 60 fps (using OBS, Loom, or Screen Studio).
- [ ] **Audio**: Clear microphone with zero background noise.
- [ ] **Browser Tabs Prepared**:
  1. `https://lastmile-ai-rails.vercel.app` (or `http://localhost:3000`) — Citizen Home & Persona Selector.
  2. `http://localhost:3000/apply` — Urdu Voice Intake & Document Upload.
  3. `http://localhost:3000/scam` & `/scam-map` — Real-Time Scam Radar & Karachi Heatmap.
  4. `http://localhost:3000/families` — Helper Multi-Family Hub & Granular Consent.
  5. `http://localhost:3000/officer` — Officer Triage Queue & Weakest-Link Inspector.
  6. `http://localhost:3000/auditor` — Cryptographic Hash-Chain Blockchain Visualizer.
  7. `https://rahbar-backend.duckdns.org/api/v1/health` — Live AWS Production Healthcheck (`audit_chain_valid: true`).
  8. `https://github.com/Naresh-Kumar17/lastmile-ai-rails` — GitHub Repository & 462/462 Passed CI Badge.

---

## 2. Complete 5-Minute Scene-by-Scene Script & Storyboard

```mermaid
timeline
    title 5-Minute Submission Video Flow
    0:00 - 0:45 : The Problem & Mission Hook : Last-Mile Crisis in Pakistan
    0:45 - 1:45 : Persona 1 - The Widow (Voice Intake) : Whisper STT + OCR + Offline Drafting
    1:45 - 2:30 : Persona 2 - The Shopkeeper (Scams) : ML Scam Radar + Karachi Geospatial Threat Map
    2:30 - 3:15 : Persona 3 - The Helper (Multi-Family) : 1 Phone 40 Families + Granular Consent Take-Back
    3:15 - 4:15 : Personas 4, 5 & 6 - Engine, Officer & Auditor : Tri-State Decision + SHA-256 Chain + AWS EC2
    4:15 - 4:45 : Conclusion & Architectural Proof : 462 Tests Passed + Zero Silent Failure
```

---

### Scene 1: The Problem & The Rahbar Mission Hook (0:00 - 0:45)

**On Screen**: Title Banner with Rahbar (رہبر) branding, followed by rapid headline shots of flood relief delays, literacy statistics in Pakistan, and fraudulent SMS scams.

**Voiceover (Speaker 1 - Confident, Engaging)**:
> *"Digital governance in Pakistan has world-class infrastructure—NADRA for identity, Raast for instant payments, and BISP for relief programs. But for millions of citizens, the **last mile** is completely broken.*  
> *Over 40% of flood victims and vulnerable widows cannot read complex government portals. Predatory scammers impersonating relief programs drain life savings from shopkeepers every single day. And community helpers in rural union councils are forced to manage 40 families from a single shared phone with zero data privacy.*  
> *Meet **Rahbar (رہبر)**: Sovereign AI on Public Rails. We designed Rahbar to ensure that low-literacy citizens, rural helpers, and government oversight officers can complete relief claims end-to-end—even on 2G connections, with zero reading required, and with mathematical tamper-proof accountability."*

---

### Scene 2: Persona 1 — The Widow (Parveen Bibi) & Voice Intake (0:45 - 1:45)

**On Screen**: Navigate to `/apply`. Toggle **Low-Bandwidth Mode** (notice shadows and heavy assets strip away instantly for 2G networks). Show clear Urdu Nastaliq / Naskh typography.

**Action**: Click the microphone icon. Play/speak the Urdu sample voice audio:
> *"میرا نام پروین بی بی ہے۔ میرے شوہر کا انتقال ہو گیا ہے، گھر میں تین بچے ہیں اور ماہانہ آمدنی بارہ ہزار روپے ہے۔ برائے مہربانی امداد دی جائے۔"*

**On Screen Highlight**:
1. Live speech audio visualizer reacts.
2. Whisper Large-v3 transcribes the audio into bilingual Roman-Urdu and Urdu Nastaliq.
3. Structured AI Extraction auto-fills the claim form:
   - Name: `Parveen Bibi`
   - Household Size: `4`
   - Monthly Income: `12,000 PKR`
4. Attach CNIC and electricity bill images $\to$ Laplacian blur score evaluates document sharpness ($> 1000$) and confirms zero image tampering.
5. Demonstrate **Offline-First Resilience**: Disable network in Chrome DevTools $\to$ submit claim $\to$ PWA saves to local IndexedDB queue and automatically synchronizes with idempotency keys as soon as connection is restored.

**Voiceover**:
> *"Here is Parveen Bibi, a widow in Sindh who cannot read. Through Rahbar's voice-first PWA, she simply speaks in natural Urdu. Our bilingual Whisper pipeline transcribes her dialect, normalizes colloquial numerals like 'barah hazaar', and extracts a structured claim automatically.*  
> *Notice our Low-Bandwidth Mode that runs seamlessly on edge 2G networks, and our offline sync queue that guarantees no citizen loses their drafted claim during connectivity dropouts."*

---

### Scene 3: Persona 2 — The Shopkeeper (Muhammad Aslam) & Scam Threat Radar (1:45 - 2:30)

**On Screen**: Navigate to `/scam` and then `/scam-map`.

**Action**:
1. Paste a typical predatory message into the Scam Radar:
   `"Benazir Income Support Program: Mubarak ho! Aapko 25,000 PKR relief grant mil gaya hai. Fauri payment lene ke liye is number pe 1000 PKR advance fee bhejein aur apna OTP share karein."`
2. Click **Classify Threat**.
3. Instant result: **CRITICAL RISK (99.4% Scam Probability)**.
4. Highlight explainable trigger tags: `[ADVANCE_FEE_FRAUD]`, `[OTP_CREDENTIAL_HARVESTING]`, `[GOVERNMENT_IMPERSONATION]`.
5. Switch to `/scam-map`: Showcase the geospatial threat intelligence map of Karachi with clustering across Malir, Korangi, Lyari, and Saddar.

**Voiceover**:
> *"Next is Muhammad Aslam, a shopkeeper who receives dozens of fraudulent SMS messages every week. Rahbar features a real-time Scam Threat Radar powered by calibrated NLP and TF-IDF classifiers.*  
> *In milliseconds, it analyzes the semantic intent, flags advance-fee and OTP-harvesting tactics with explainable tags in both English and Urdu, and maps active phishing campaigns across Karachi districts on our live Geospatial Threat Map to protect entire communities before money is stolen."*

---

### Scene 4: Persona 3 — Community Helper & Granular Consent Take-Back (2:30 - 3:15)

**On Screen**: Navigate to `/families` and `/consent`.

**Action**:
1. Open Helper Mode: Show 40 managed families on a single smartphone.
2. Switch active family context with 2 taps $\to$ show strict session and consent boundary isolation.
3. Open the **Granular Consent Ledger**:
   - Scopes: `identity`, `income`, `bills`, `helper_acting`, `documents`.
   - Withdraw `income` consent for `cit_parveen`.
   - Attempt to query Parveen's income from another role or session $\to$ **Immediate HTTP 403 ConsentWithdrawnException**.

**Voiceover**:
> *"In rural areas, one community helper often assists dozens of families from a single mobile device. Rahbar's Helper Mode provides instant 2-tap context switching with cryptographic session isolation.*  
> *Even more critically, Challenge 06 requires 'Consent and Take-Back'. In Rahbar, citizens hold granular data sovereignty: identity, income, utility bills, and helper permissions are separately authorized.*  
> *When Parveen withdraws consent for her income data, our backend Consent Gateway enforces an authoritative database lock—instantly terminating all future read access across every worker process with a hard HTTP 403."*

---

### Scene 5: Decision Engine, Officer Review & Cryptographic Auditor Ledger (3:15 - 4:15)

**On Screen**:
1. Navigate to `/officer` (Review Queue).
2. Navigate to `/auditor` (Audit Timeline).
3. Switch to terminal / browser showing `https://rahbar-backend.duckdns.org/api/v1/health`.

**Action**:
1. **Tri-State Decision Engine**: Show how clean claims receive **Auto-Approve** ($p \ge 0.85$) with an HMAC-signed approval token for instant mock Raast payment.
2. Borderline cases with blurred bills are **NEVER auto-rejected**; they trigger **Ask More Proof** or route to the **Human Review Queue** where the weakest link (e.g. OCR blur score) is surfaced.
3. Open `/auditor`: Inspect the live SHA-256 hash-chained audit ledger.
4. Show the live AWS Production Health Endpoint:
   `https://rahbar-backend.duckdns.org/api/v1/health`
   Highlight:
   - `"status": "healthy"`
   - `"audit_chain_valid": true`
   - `"total_audit_records": 830`
   - `"audit_head_hash": "a9de86916241..."`
   - DPI Rails: NADRA, Raast, Complaints all `"OPERATIONAL"`.
5. Mention PostgreSQL database append-only triggers (`trg_audit_log_append_only`) preventing any illegal UPDATE or DELETE.

**Voiceover**:
> *"When a claim is evaluated, Rahbar follows our cost-calibrated decision philosophy: a wrongful rejection is ten times more harmful than a slow decision. High-confidence claims are auto-approved with cryptographic disbursement tokens on our mock Raast rail.*  
> *Uncertain cases never guess—they route to our Officer Cockpit with the exact weakest link highlighted.*  
> *Every single action—from consent grants to payments—is sealed into an HMAC-SHA256 linked cryptographic ledger. Our live production deployment on AWS EC2 is backed by PostgreSQL 16 with database-level append-only triggers that physically reject any modification or tampering.*  
> *As verified live right now on our public domain, all 830 audit records are 100% mathematically valid."*

---

### Scene 6: Conclusion, Engineering Rigor & Impact (4:15 - 4:45)

**On Screen**: GitHub Actions CI page showing green workflows, 462/462 tests passed, zero lint errors, and the GitHub repository README.

**Voiceover**:
> *"Rahbar is not a mock concept—it is a fully engineered, production-deployed Digital Public Infrastructure platform.*  
> *With Next.js 14, asynchronous FastAPI, PostgreSQL 16, and an adversarial test suite of **462 automated tests passing with 100% coverage**, we have built sovereign AI that is explainable, resilient, and accessible to the most vulnerable citizens of Pakistan.*  
> *Thank you, judges of Coder's Cup '26. With Rahbar, no citizen is left behind, no relief rupee is stolen, and every decision is accountable."*

---

## 3. Quick Video Rehearsal Tips for the Team

1. **Keep it brisk**: Don't linger on form typing—use pre-filled test buttons or copy-paste text so the video flows dynamically.
2. **Show the live domain**: Point out `https://rahbar-backend.duckdns.org` in the URL bar to prove it's live in the cloud on AWS.
3. **Show the Urdu Voice & Scam Map**: These are visual showstoppers that immediately stand out to judges.
4. **Mention the 462 passing tests & append-only database triggers**: This proves production-grade engineering over fragile prototypes.
