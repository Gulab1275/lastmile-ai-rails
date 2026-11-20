# Coder's Cup 2026 — AI Hackathon
**ACM NUCES · FAST-NUCES Karachi**  
**Official Challenge Brief / November 2026**

# The Last Mile: AI on Public Rails
*A 48-hour hackathon on digital public infrastructure (DPI)*

| Detail | Specification |
| :--- | :--- |
| **Build Window** | Friday, 20 November 2026, 6:00 PM – Sunday, 22 November 2026, 6:00 PM PKT |
| **Development Mode** | Remote · 48 hours |
| **Final Evaluation** | Monday, 23 November 2026 · FAST-NUCES Karachi Library · exact time to be announced |
| **Team Size** | 3–4 participants |

> **PROTOTYPE ONLY.** Everything you build is a prototype. It is not an official service.

---

## Note to Participants
* You are free to use any AI tool and any AI model to help you code. But the judges will not score how fast you code. They will score your judgment: **how your system handles risk, mistakes, and surprises**.
* You are scored on how your system behaves, not on what you claim.
* **Use of real personal data will result in disqualification. Mock everything.**
* All development must take place during the hackathon. Solutions must be original; plagiarism and pre-built projects are prohibited.

---

## 01 Background
Pakistan has developed digital public infrastructure (DPI) through systems for identity verification, digital payments, and data exchange. Initiatives such as NADRA and Raast demonstrate how these systems form the foundation of essential digital services.

However, the existence of digital infrastructure does not guarantee that everyone can access or use it effectively. Many people still face barriers such as low literacy, language difficulties, complicated forms, and unreliable internet connectivity.

Trust and safety present another challenge. Fraudulent messages, misleading information, and uncertainty about the legitimacy of digital services can discourage people from using systems designed to help them.

These challenges highlight two critical gaps: **accessibility** and **trust**. Bridging the last mile requires making digital public services not only available, but also understandable, accessible, and safe for the people who need them most.

---

## 02 The Challenge
Meet three people. They all depend on the same public services:
* **The widow** cannot read forms and has a weak phone signal.
* **The shopkeeper** keeps getting fake "relief payment" messages.
* **The helper** serves 40 families from one shared phone.

Their records are incomplete. Their names are spelled in different ways. One wrong approval can cost someone their savings.

Build one multi-user SaaS platform that serves all three. It must decide, explain, and protect. It must also be able to say "I am not sure" and hand the case to a human.

**This is not a chatbot. It is a working platform with users, roles, cases, rules, and audit trails.**

### Complete this sentence before you code:
> **We help [specific person] do [one public task] even though [what stops them today].**

*Pick one task and finish it end to end. A deep solution for one task beats a thin solution for many.*

---

## 03 Core Requirements

### Constraints (Your system must handle all of these):
1. **Wrong approvals cost more than slow approvals:** Show how your system handles this trade-off.
2. **Weak internet:** The system must work on a slow or dropping connection.
3. **Low literacy:** The system must be usable by someone who cannot read.
4. **Rules change without notice:** The system must adapt without code changes.
5. **Bad data:** Data will be missing, duplicated, or wrong. Do not assume clean input.
6. **Explainable decisions:** Every AI decision must be explainable to the user and reviewable by an auditor.
7. **User control:** Users must control what data is shared and be able to take it back.
8. **"I am not sure":** When confidence is low, the system must stop and hand over to a human.

---

## 04 Scope: Roles, Platform & AI Features

### User Roles (Use at least 3)
* **Citizen:** Upload documents, use voice or text, track tasks, control data sharing.
* **Community Helper:** Assist many citizens, manage cases with proper permissions.
* **Department Officer:** Review, approve, or reject claims and complaints.
* **Admin:** Manage users, roles, rules, and mock services.
* **Auditor:** Read-only access to logs, consent records, and AI decisions.

### Platform Features
**Core (All required):**
* Secure login (JWT or OAuth) with role-based access control
* Dashboard with task progress, status, and history
* Case management (create, assign, escalate, close)
* Public REST API with API keys and documentation (Swagger or OpenAPI)
* Audit log of every user, AI, and agent action
* Consent management (see, share, withdraw, correct data)
* Mock identity, payment, and data services behind clean APIs

**Pick at least 3 (Rahbar does 5):**
* Multi-tenant workspaces
* Admin rule editor (change eligibility rules without code changes)
* Notifications (SMS, WhatsApp, email, in-app)
* Webhooks for outside systems
* Analytics dashboard per tenant
* Officer review queue with priority and confidence sorting
* Subscription plans and usage limits
* Background jobs and queues
* Rate limiting and error handling
* Low-bandwidth or offline mode

### AI Features (Use at least 3 — Rahbar implements all):
* **RAG:** Answer from official rules, forms, and policies, with sources shown.
* **Autonomous agents + tool calling:** Plan and finish a task step by step by calling mock identity, payment, and complaint APIs.
* **Classification and routing (Jev style):** Sort scams, complaints, and requests with confidence scores and routing.
* **Computer vision:** Read IDs and forms (OCR), check QR codes, detect forged or edited documents, handle blurry photos.
* **Voice:** Speech-to-text and text-to-speech in Urdu or a regional language.
* **Structured outputs:** Fill forms in a fixed format and validate them (Pydantic / JSON schema).
* **Guardrails + human approval:** Block unsafe answers, flag unsure cases, require approval for risky steps.
* **Explainability:** Tell users in simple words why a decision was made.
* **Anomaly detection:** Spot suspicious payments, repeated claims, or unusual patterns.
* **Memory and context:** Remember progress across steps and sessions.
* **Evaluation dashboard:** Show accuracy, false alarms, speed, cost, and failures.

### Engineering Basics:
* Database with migrations (Postgres or Supabase)
* Deployed live link
* Monitoring, logs, and basic tests

---

## 05 Technical Challenges
* **CHALLENGE 01 — The Cost of Being Wrong:** Define your own rule for when the system acts alone, when it asks for more proof, and when it sends the case to a human. Show the numbers behind your choice.
* **CHALLENGE 02 — Saying "I Am Not Sure":** Low confidence must lead to a clear handoff to a human with case notes attached. Silent guessing earns zero.
* **CHALLENGE 03 — Bad Data:** Missing fields, duplicate people, and names spelled in many ways (e.g., Muhammad / Mohammad / Muhammed). Handle them without crashing and without a wrong match.
* **CHALLENGE 04 — Rules That Change:** An admin changes an eligibility rule. The system must follow the new rule at once, with no code change and no redeploy. Old decisions must still show which rule version was used.
* **CHALLENGE 05 — Explain and Audit:** Every AI decision needs two views: a simple reason for the user, and a full trace for the auditor (input, rule/model version, confidence, result).
* **CHALLENGE 06 — Consent and Take-Back:** A user can see who has their data, change what is shared, and withdraw it. Withdrawal must truly stop access, and the audit log must show it.
* **CHALLENGE 07 — Works for Everyone:** A person who cannot read, on a weak connection, must still finish the task (voice, icons, small pages, saved progress).
* **CHALLENGE 08 — Scams and Fake Documents:** Catch fake "relief payment" messages and edited or forged documents. Show false alarms honestly.

---

## 06 Creative Features (Bonus)
* **Digital Twin:** Safe copy of your system where an admin can test a rule change on past cases and see the effect before it goes live.
* **Helper Mode:** One shared phone, 40 families. Fast and safe switching between people, with separate consent for each.
* **Offline-First Sync:** Work with no signal. Sync later without losing or duplicating data.
* **Scam Map:** Live view of scam patterns by type, area, or time, built from classified messages.

---

## 07 Rules & Submission
* Build during the event.
* Any tools and AI models are allowed.
* Mock all identity, payment, and data services. No real personal data.
* Label your project as a prototype, not an official service.
* Tell the judges what is real and what is simulated.

### What to Submit:
1. Functional AI-powered prototype and **live demo**
2. Code repository (**GitHub repository link**)
3. A **README file**
4. Demonstration video (**public Google Drive link**)
5. Presentation slides (optional)

---

## 08 Judging Notes
* **Functionality over claims:** Judges evaluate actual behavior and functionality rather than slides.
* **Security and reliability:** Server-side enforcement of access controls and permissions (show HTTP 403 on forbidden paths).
* **Live demonstration:** Mandatory. Screenshots cannot substitute for demonstrating the actual system.
* **Responsible AI behavior:** Systems must recognize uncertainty and demonstrate appropriate human intervention.
* **Technical judgment:** Prepared to explain and justify architectural decisions and system limitations.
