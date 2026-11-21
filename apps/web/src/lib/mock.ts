import type {
  Role, TokenResponse, ConsentScope, ConsentStatus, ConsentRecord,
  CaseItem, ReviewQueueItem, ScamCheckResponse, RuleSet, AuditEntry,
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

// ---------- Consent ----------
const consents: Record<string, ConsentRecord[]> = {};

function ensureConsents(citizenId: string): ConsentRecord[] {
  if (!consents[citizenId]) {
    consents[citizenId] = (["identity", "income"] as ConsentScope[]).map((scope) => ({
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

// ---------- Cases ----------
const comps = { identity: 0.97, ocr: 0.95, authenticity: 0.98, rules_complete: 1, scam_safety: 0.99 };
const cases: CaseItem[] = [
  {
    id: "case-A", citizen_id: "mock-citizen_parveen", citizen_name: "Parveen Bibi",
    cnic: "42101-1234567-1", phone: "0300-1112223", household_size: 5, monthly_income: 18000,
    benefit_type: "relief_cash_grant", requested_amount: 12000, status: "approved",
    decision: {
      case_id: "case-A", route: "auto_approve", confidence: 0.95, components: comps, missing: [],
      reason_simple: { en: "All documents are clear. Approved.", ur: "تمام کاغذات واضح ہیں۔ منظور۔" },
      rule_version: 3,
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
      reason_simple: { en: "Your electricity bill photo is blurry. Please upload it again.", ur: "بجلی کے بل کی تصویر دھندلی ہے۔ دوبارہ اپ لوڈ کریں۔" },
      rule_version: 3,
    },
    created_at: now(), updated_at: now(),
  },
  {
    id: "case-C", citizen_id: "mock-citizen_c", citizen_name: "Bashir Ahmed",
    cnic: "35202-1112223-5", phone: "0333-9998887", household_size: 7, monthly_income: 30000,
    benefit_type: "relief_cash_grant", requested_amount: 25000, status: "in_review",
    decision: {
      case_id: "case-C", route: "human_review", confidence: 0.41,
      components: { ...comps, identity: 0.41 }, missing: [],
      reason_simple: { en: "Name does not match national records. An officer will check.", ur: "نام قومی ریکارڈ سے نہیں ملتا۔ افسر جانچ کرے گا۔" },
      rule_version: 3,
    },
    created_at: now(), updated_at: now(),
  },
];

function queue(): ReviewQueueItem[] {
  return cases.filter((c) => c.status === "in_review").map((c) => ({
    case_id: c.id, citizen_name: c.citizen_name, cnic: c.cnic,
    requested_amount: c.requested_amount, confidence: c.decision?.confidence ?? 0,
    priority_score: 8.2, status: c.status,
    handoff_packet: {
      flags: ["Identity mismatch", "High requested amount"],
      suggested_action: "Verify CNIC photo against NADRA record",
      component_breakdown: c.decision?.components ?? comps,
    },
    submitted_at: c.created_at,
  }));
}

// ---------- Rules / audit ----------
let rules: RuleSet = { version: 3, name: "Standard Relief Policy", max_monthly_income: 35000, is_active: true };

const audit: AuditEntry[] = Array.from({ length: 6 }, (_, i) => ({
  id: `a${i}`, prev_hash: `${i}`.repeat(8), current_hash: `${i + 1}`.repeat(8),
  timestamp: now(), actor: "officer_aslam", actor_role: "officer",
  action: ["login", "consent_grant", "case_create", "decision_evaluate", "review_approve", "consent_withdraw"][i],
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

export async function mockRequest(endpoint: string, options: RequestInit = {}): Promise<unknown> {
  await wait(300);
  const body = JSON.parse(String(options.body ?? "{}"));
  const method = (options.method ?? "GET").toUpperCase();

  if (endpoint === "/auth/login") {
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

  if (endpoint.startsWith("/consent/status/")) {
    return consentStatus(endpoint.split("/").pop() as string);
  }
  if (endpoint === "/consent/grant" || endpoint === "/consent/withdraw") {
    const list = ensureConsents(body.citizen_id);
    const granting = endpoint === "/consent/grant";
    const found = list.find((c) => c.scope === body.scope);
    if (found) {
      found.granted = granting;
      if (granting) { found.granted_at = now(); found.revoked_at = null; }
      else found.revoked_at = now();
    } else {
      list.push({
        id: `c-${body.citizen_id}-${body.scope}`, citizen_id: body.citizen_id, scope: body.scope,
        granted: granting, granted_at: now(), revoked_at: granting ? null : now(),
      });
    }
    return { citizen_id: body.citizen_id, scope: body.scope, granted: granting };
  }

  if (endpoint === "/ai/scam-check") return scamCheck(String(body.text ?? ""));

  if (endpoint === "/cases" && method === "GET") return cases;
  if (endpoint === "/cases" && method === "POST") {
    const created: CaseItem = {
      id: `case-${Date.now()}`, citizen_id: "mock-citizen", ...body,
      benefit_type: body.benefit_type ?? "relief_cash_grant",
      requested_amount: body.requested_amount ?? 12000,
      status: "submitted", created_at: now(), updated_at: now(),
    };
    cases.unshift(created);
    return created;
  }
  if (endpoint.startsWith("/cases/")) {
    const c = cases.find((x) => x.id === endpoint.split("/")[2]);
    if (!c) throw { message_en: "Case not found", message_ur: "کیس نہیں ملا" };
    return c;
  }

  if (endpoint === "/review/queue") return queue();
  if (endpoint.startsWith("/review/") && endpoint.endsWith("/decision")) {
    const c = cases.find((x) => x.id === endpoint.split("/")[2]);
    if (c) c.status = body.approved ? "disbursed" : "rejected";
    return { case_id: c?.id, status: c?.status };
  }

  if (endpoint === "/rules/active") return rules;
  if (endpoint === "/rules/publish") { rules = { ...body.rule_set, version: rules.version + 1 }; return rules; }
  if (endpoint === "/digital-twin/simulate") {
    const newMax = Number(body.draft_rule_set?.max_monthly_income ?? rules.max_monthly_income);
    const delta = (newMax - rules.max_monthly_income) / 1000 * 0.012;
    return {
      total_cases_simulated: body.sample_size ?? 100, previous_rule_version: rules.version,
      draft_rule_version: rules.version + 1, previous_approval_rate: 0.62,
      projected_approval_rate: Math.min(1, Math.max(0, 0.62 + delta)), approval_rate_delta: delta,
      impact_summary: `Raising the income limit to Rs ${newMax} changes approvals by ${(delta * 100).toFixed(1)}%.`,
      affected_case_ids: ["case-B", "case-C"],
    };
  }

  if (endpoint === "/audit/logs") return audit;
  if (endpoint === "/audit/verify-chain") {
    return { is_valid: true, total_records: audit.length, head_hash: audit[audit.length - 1].current_hash };
  }

  if (endpoint === "/ai/eval-summary") {
    return {
      threshold_sweep: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map((t) => ({
        threshold: t, expected_cost: Math.round(100 - 80 * Math.exp(-((t - 0.5) ** 2) / 0.05)),
      })),
    };
  }

  throw { message_en: `No mock data yet for ${endpoint}` };
}