import type {
  Role, TokenResponse, ConsentScope, ConsentStatus, ConsentRecord, CaseItem,
  ReviewQueueItem, ScamCheckResponse, RuleSet, AuditEntry, Decision, Family,
} from "./api";

// Fake backend for local UI work (NEXT_PUBLIC_USE_MOCK=true).
// Shapes match the real API so you can switch to the backend with no UI changes.

const USERS: Record<string, Role> = {
  citizen_parveen: "citizen",
  citizen_tariq: "citizen",
  helper_shazia: "helper",
  officer_aslam: "officer",
  admin_ayesha: "admin",
  auditor_iqbal: "auditor",
};

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString();
const ls = (k: string) => (typeof window === "undefined" ? "" : localStorage.getItem(k) ?? "");

// ---------- Consent ----------
const consents: Record<string, ConsentRecord[]> = {};

function ensureConsents(citizenId: string): ConsentRecord[] {
  if (!consents[citizenId]) {
    const scopes: ConsentScope[] = ["identity", "income", "helper_acting"];
    consents[citizenId] = scopes.map((scope) => ({
      id: `c-${citizenId}-${scope}`, citizen_id: citizenId, scope,
      granted: true, granted_at: now(), revoked_at: null, audit_hash: null,
    }));
  }
  return consents[citizenId];
}

function consentStatus(citizenId: string): ConsentStatus {
  const all = ensureConsents(citizenId);
  const active = all.filter((c) => c.granted).map((c) => c.scope);
  const revoked = all.filter((c) => !c.granted).map((c) => c.scope);
  return {
    citizen_id: citizenId, active_scopes: active, revoked_scopes: revoked,
    all_consents: all, can_helper_act: active.includes("helper_acting"),
  };
}

// ---------- Helper families (40) ----------
const NAMES = ["Parveen Bibi", "Mohammad Tariq", "Bashir Ahmed", "Zainab Khatoon", "Abdul Rehman", "Nasreen Akhtar",
  "Imran Shah", "Rukhsana Bibi", "Ghulam Mustafa", "Salma Parveen"];
const families: Family[] = Array.from({ length: 40 }, (_, i) => ({
  id: `mock-family-${i + 1}`,
  name: `${NAMES[i % NAMES.length]} ${i >= NAMES.length ? `(${Math.floor(i / NAMES.length) + 1})` : ""}`.trim(),
  cnic: `42101-${String(1000000 + i * 37).slice(0, 7)}-${(i % 9) + 1}`,
}));

// ---------- Rules ----------
let rules: RuleSet = {
  version: 3, name: "Standard Relief Policy", max_monthly_income: 35000, min_household_size: 1,
  max_auto_approve_amount: 15000, requires_valid_cnic: true, requires_utility_bill: true,
  max_wrong_prob_auto_approve: 0.05, max_wrong_prob_ask_proof: 0.3, is_active: true,
};
const ruleHistory: RuleSet[] = [
  { ...rules, version: 1, max_monthly_income: 30000, is_active: false },
  { ...rules, version: 2, max_monthly_income: 32000, is_active: false },
  rules,
];

// ---------- Cases ----------
const comps = { identity: 0.97, ocr: 0.95, authenticity: 0.98, rules_complete: 1, scam_safety: 0.99 };
const cases: CaseItem[] = [
  {
    id: "case-A", citizen_id: "mock-citizen_parveen", citizen_name: "Parveen Bibi",
    cnic: "42101-1234567-1", phone: "0300-1112223", household_size: 5, monthly_income: 18000,
    benefit_type: "relief_cash_grant", requested_amount: 12000, status: "approved",
    decision: {
      case_id: "case-A", route: "auto_approve", confidence: 0.95, components: comps, missing: [],
      reason_simple: { en: "All documents are clear. Approved.", ur: "تمام کاغذات واضح ہیں۔ منظور۔" }, rule_version: 3,
    },
    created_at: now(), updated_at: now(),
  },
  {
    id: "case-B", citizen_id: "mock-citizen_tariq", citizen_name: "Mohammad Tariq",
    cnic: "42201-7654321-3", phone: "0321-5556667", household_size: 3, monthly_income: 22000,
    benefit_type: "ration_subsidy", requested_amount: 8000, status: "need_proof",
    decision: {
      case_id: "case-B", route: "ask_more_proof", confidence: 0.62,
      components: { ...comps, ocr: 0.62 }, missing: ["Electricity bill (blurry)"],
      reason_simple: { en: "Your electricity bill photo is blurry. Please upload it again.", ur: "بجلی کے بل کی تصویر دھندلی ہے۔ دوبارہ اپ لوڈ کریں۔" }, rule_version: 3,
    },
    created_at: now(), updated_at: now(),
  },
  {
    id: "case-C", citizen_id: "mock-family-3", citizen_name: "Bashir Ahmed",
    cnic: "35202-1112223-5", phone: "0333-9998887", household_size: 7, monthly_income: 30000,
    benefit_type: "relief_cash_grant", requested_amount: 25000, status: "in_review",
    decision: {
      case_id: "case-C", route: "human_review", confidence: 0.41,
      components: { ...comps, identity: 0.41 }, missing: [],
      reason_simple: { en: "Name does not match national records. An officer will check.", ur: "نام قومی ریکارڈ سے نہیں ملتا۔ افسر جانچ کرے گا۔" }, rule_version: 3,
    },
    created_at: now(), updated_at: now(),
  },
];

function evaluate(c: CaseItem): Decision {
  const limit = rules.max_monthly_income;
  let route: Decision["route"] = "auto_approve";
  let confidence = 0.92;
  let en = "All checks passed. Approved.";
  let ur = "تمام جانچ مکمل۔ منظور۔";
  let missing: string[] = [];
  if (c.monthly_income > limit * 1.2) {
    route = "human_review"; confidence = 0.4;
    en = "Income is far above the limit. An officer will check."; ur = "آمدنی حد سے بہت زیادہ ہے۔ افسر جانچ کرے گا۔";
  } else if (c.monthly_income > limit) {
    route = "ask_more_proof"; confidence = 0.6; missing = ["Income proof"];
    en = "Income is slightly above the limit. Please send income proof."; ur = "آمدنی حد سے تھوڑی زیادہ ہے۔ آمدنی کا ثبوت بھیجیں۔";
  }
  return {
    case_id: c.id, route, confidence, components: { ...comps, rules_complete: confidence },
    missing, reason_simple: { en, ur }, rule_version: rules.version,
  };
}

function queue(): ReviewQueueItem[] {
  return cases.filter((c) => c.status === "in_review").map((c) => ({
    case_id: c.id, citizen_name: c.citizen_name, cnic: c.cnic,
    requested_amount: c.requested_amount, confidence: c.decision?.confidence ?? 0,
    priority_score: 8.2 - (c.decision?.confidence ?? 0), status: c.status,
    handoff_packet: {
      flags: ["Identity mismatch", "High requested amount"],
      suggested_action: "Verify CNIC photo against NADRA record",
      component_breakdown: c.decision?.components ?? comps,
    },
    submitted_at: c.created_at,
  }));
}

// ---------- Audit ----------
const audit: AuditEntry[] = Array.from({ length: 8 }, (_, i) => ({
  id: `a${i}`, prev_hash: `${(i * 7919).toString(16).padStart(8, "0")}`, current_hash: `${((i + 1) * 7919).toString(16).padStart(8, "0")}`,
  timestamp: now(), actor: i % 2 ? "officer_aslam" : "helper_shazia", actor_role: i % 2 ? "officer" : "helper",
  action: ["login", "consent_grant", "case_create", "decision_evaluate", "review_approve", "consent_withdraw", "rule_publish", "case_submit"][i],
  resource_id: "case-C", result: "ok",
}));

function scamCheck(text: string): ScamCheckResponse {
  const t = text.toLowerCase();
  const hits: string[] = [];
  if (/http|bit\.ly|www\./.test(t)) hits.push("Contains a suspicious link");
  if (/otp|pin|password|پاس ورڈ/.test(t)) hits.push("Asks for OTP / PIN / password");
  if (/prize|winner|inaam|انعام|جیت/.test(t)) hits.push("Prize or lottery wording");
  if (/urgent|فوری|abhi|immediately/.test(t)) hits.push("Creates false urgency");
  if (/cnic|شناختی/.test(t) && hits.length) hits.push("Asks for CNIC details");
  if (hits.length >= 2) return { label: "scam", confidence: 0.94, reasons: hits };
  if (hits.length === 1) return { label: "unsure", confidence: 0.55, reasons: hits };
  return { label: "legit", confidence: 0.9, reasons: ["No scam patterns found"] };
}

function evalSummary() {
  const thresholds = [0.01, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4];
  const curve = thresholds.map((t) => {
    const auto = Math.floor(200 * Math.min(0.9, t * 2.2 + 0.15));
    const wrong = t > 0.04 ? Math.floor((t - 0.04) * 85) : 0;
    const human = Math.floor(Math.max(10, 200 - auto - t * 50));
    const ask = Math.max(5, 200 - auto - human);
    return {
      threshold: t, auto_approve_count: auto, wrong_approvals: wrong, human_reviews: human, ask_proofs: ask,
      expected_cost_per_case: Math.round(((10 * wrong + human + 0.4 * ask) / 200) * 1000) / 1000,
    };
  });
  const best = curve.reduce((a, b) => (b.expected_cost_per_case < a.expected_cost_per_case ? b : a));
  return {
    total_test_samples: 200,
    scam_classifier_metrics: {
      accuracy: 0.985, precision: 0.99, recall: 0.98, f1_score: 0.985, false_alarm_rate: 0.01,
      confusion_matrix: { true_scam: 98, false_scam_alarm: 1, true_legit: 99, missed_scam: 2 },
    },
    identity_matcher_metrics: { exact_cnic_accuracy: 1, urdu_fuzzy_match_accuracy: 0.965, typo_tolerance_rate: 0.92, false_merge_rate: 0 },
    decision_engine_metrics: {
      optimal_p_wrong_threshold: best.threshold, min_expected_cost_per_case: best.expected_cost_per_case,
      auto_approve_rate: `${((best.auto_approve_count / 200) * 100).toFixed(1)}%`,
      human_review_rate: `${((best.human_reviews / 200) * 100).toFixed(1)}%`,
      ask_more_proof_rate: `${((best.ask_proofs / 200) * 100).toFixed(1)}%`, auto_reject_rate: 0,
    },
    threshold_sweep_curve: curve,
    system_guarantees: [
      { guarantee: "Never Auto-Reject", verified: true, detail: "Low confidence routes to an officer or asks for more proof." },
      { guarantee: "Weakest-Link Confidence", verified: true, detail: "overall = min(components)." },
      { guarantee: "Gated Cash Disbursement", verified: true, detail: "Payout needs a valid approval token." },
    ],
  };
}

export async function mockRequest(endpoint: string, options: RequestInit = {}): Promise<unknown> {
  await wait(300);
  const body = JSON.parse(String(options.body ?? "{}"));
  const method = (options.method ?? "GET").toUpperCase();
  const path = endpoint.split("?")[0];
  const parts = path.split("/"); // ["", "cases", "id", "submit"]

  if (path === "/auth/login") {
    const role = USERS[body.username];
    if (!role || body.password !== "password123") {
      throw { message_en: "Wrong username or password", message_ur: "صارف کا نام یا پاس ورڈ غلط ہے" };
    }
    const result: TokenResponse = {
      access_token: `mock-token-${body.username}`, refresh_token: "mock-refresh",
      role, user_id: `mock-${body.username}`, username: body.username,
    };
    return result;
  }

  if (path === "/helper/families") return families;

  if (path.startsWith("/consent/status/")) return consentStatus(parts[3]);
  if (path === "/consent/grant" || path === "/consent/withdraw") {
    const list = ensureConsents(body.citizen_id);
    const granting = path === "/consent/grant";
    const found = list.find((c) => c.scope === body.scope);
    if (found) {
      found.granted = granting;
      if (granting) { found.granted_at = now(); found.revoked_at = null; } else found.revoked_at = now();
    } else {
      list.push({
        id: `c-${body.citizen_id}-${body.scope}`, citizen_id: body.citizen_id, scope: body.scope,
        granted: granting, granted_at: now(), revoked_at: granting ? null : now(),
      });
    }
    return { citizen_id: body.citizen_id, scope: body.scope, granted: granting };
  }

  if (path === "/ai/scam-check") return scamCheck(String(body.text ?? ""));
  if (path === "/ai/extract-form") {
    const text = String(body.text ?? "");
    const cnic = text.match(/\d{5}-?\d{7}-?\d/)?.[0] ?? null;
    return { full_name: null, cnic, phone: text.match(/03\d{2}-?\d{7}/)?.[0] ?? null,
      household_size: null, monthly_income: null, missing_fields: ["full_name"], confidence: 0.8 };
  }
  if (path === "/ai/sync-offline-batch") {
    (body.queued_cases ?? []).forEach((q: Record<string, unknown>) =>
      cases.unshift({
        id: `case-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`, citizen_id: String(q.citizen_id ?? "mock-offline"),
        citizen_name: String(q.citizen_name), cnic: String(q.cnic), phone: String(q.phone),
        household_size: Number(q.household_size), monthly_income: Number(q.monthly_income),
        benefit_type: "relief_cash_grant", requested_amount: Number(q.requested_amount ?? 12000),
        status: "submitted", created_at: now(), updated_at: now(),
      }));
    return { batch_id: body.batch_id, synced: (body.queued_cases ?? []).length };
  }
  if (path === "/ai/eval-summary") return evalSummary();

  if (path === "/cases" && method === "GET") {
    const role = ls("role");
    return role === "citizen" ? cases.filter((c) => c.citizen_id === ls("user_id")) : cases;
  }
  if (path === "/cases" && method === "POST") {
    const created: CaseItem = {
      id: `case-${Date.now()}`, citizen_id: ls("active_citizen") || ls("user_id") || "mock-citizen",
      citizen_name: body.citizen_name, cnic: body.cnic, phone: body.phone,
      household_size: body.household_size, monthly_income: body.monthly_income,
      benefit_type: body.benefit_type ?? "relief_cash_grant", requested_amount: body.requested_amount ?? 12000,
      status: "draft", created_at: now(), updated_at: now(),
    };
    cases.unshift(created);
    return created;
  }
  if (parts[1] === "cases" && parts[2]) {
    const c = cases.find((x) => x.id === parts[2]);
    if (!c) throw { message_en: "Case not found", message_ur: "کیس نہیں ملا" };
    if (parts[3] === "submit") { c.status = "submitted"; return c; }
    if (parts[3] === "documents") return { case_id: c.id, filename: "upload", status: "received" };
    return c;
  }

  if (parts[1] === "decisions" && parts[2] === "evaluate") {
    const c = cases.find((x) => x.id === parts[3]);
    if (!c) throw { message_en: "Case not found" };
    c.decision = evaluate(c);
    c.status = c.decision.route === "auto_approve" ? "approved" : c.decision.route === "ask_more_proof" ? "need_proof" : "in_review";
    return c.decision;
  }
  if (parts[1] === "decisions" && parts[2] === "explain") {
    const c = cases.find((x) => x.id === parts[3]);
    if (!c?.decision) throw { message_en: "Case or decision not found. Please evaluate first." };
    return {
      case_id: c.id, view: "auditor", rule_version: c.decision.rule_version, route: c.decision.route,
      overall_confidence: c.decision.confidence, component_confidences: c.decision.components,
      weakest_link: "min(components)", inputs: { monthly_income: c.monthly_income, household_size: c.household_size },
      audit_hash: audit[audit.length - 1].current_hash,
    };
  }

  if (path === "/review/queue") return queue();
  if (parts[1] === "review" && parts[3] === "decision") {
    const c = cases.find((x) => x.id === parts[2]);
    if (c) { c.status = body.approved ? "disbursed" : body.decision === "ask_more_proof" ? "need_proof" : "rejected"; c.officer_notes = body.mandatory_officer_notes; }
    return { case_id: c?.id, status: c?.status };
  }

  if (path === "/rules/active") return rules;
  if (path === "/rules/versions") {
    return ruleHistory.map((r) => ({ version: r.version, name: r.name, is_active: r.version === rules.version, rule_set: r, created_at: now() }));
  }
  if (path === "/rules/publish") {
    rules = { ...body, version: rules.version + 1, is_active: true };
    ruleHistory.push(rules);
    return rules;
  }
  if (path === "/digital-twin/simulate") {
    const d = body.draft_rule_set as RuleSet;
    const delta = ((d.max_monthly_income - rules.max_monthly_income) / 1000) * 0.012
      + ((d.max_auto_approve_amount - rules.max_auto_approve_amount) / 1000) * 0.004;
    const projected = Math.min(1, Math.max(0, 0.62 + delta));
    return {
      total_cases_simulated: body.sample_size ?? 100, previous_rule_version: rules.version,
      draft_rule_version: rules.version + 1, previous_approval_rate: 0.62, projected_approval_rate: projected,
      approval_rate_delta: delta,
      impact_summary: `With this change about ${Math.abs(Math.round(delta * (body.sample_size ?? 100)))} of ${body.sample_size ?? 100} sample cases would ${delta >= 0 ? "newly qualify" : "stop qualifying"}.`,
      affected_case_ids: ["case-B", "case-C"],
    };
  }

  if (path === "/audit/logs") return audit;
  if (path === "/audit/verify-chain") {
    return { is_valid: true, total_records: audit.length, head_hash: audit[audit.length - 1].current_hash };
  }

  throw { message_en: `No mock data yet for ${endpoint}` };
}