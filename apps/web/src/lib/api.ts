import { mockRequest } from "./mock";

/**
 * Rahbar API client (Next.js / PWA).
 * Endpoints match docs/openapi.json.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

// ---------- Types (match services/shared/schemas.py) ----------
export type Role = "citizen" | "helper" | "officer" | "admin" | "auditor";
export type ConsentScope = "identity" | "income" | "bills" | "helper_acting";
export type ScamLabel = "scam" | "legit" | "unsure";
export type RouteDecision = "auto_approve" | "ask_more_proof" | "human_review";
export type CaseStatus =
  | "draft" | "submitted" | "in_review" | "approved" | "rejected"
  | "need_more_info" | "processing" | "need_proof" | "disbursed";

export interface ApiError {
  message_en?: string;
  message_ur?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  role: Role;
  user_id: string;
  username: string;
}

export interface CaseCreate {
  citizen_name: string;
  cnic: string;
  phone: string;
  household_size: number;
  monthly_income: number;
  benefit_type?: string;
  requested_amount?: number;
  address?: string;
  helper_id?: string;
  notes?: string;
}

export interface ScamCheckResponse {
  label: ScamLabel;
  confidence: number;
  reasons: string[];
}

export interface ConsentRecord {
  id: string;
  citizen_id: string;
  scope: ConsentScope;
  granted: boolean;
  granted_to_helper_id?: string | null;
  granted_at: string;
  revoked_at?: string | null;
  audit_hash?: string | null;
}

export interface ConsentStatus {
  citizen_id: string;
  active_scopes: ConsentScope[];
  revoked_scopes: ConsentScope[];
  all_consents: ConsentRecord[];
  can_helper_act: boolean;
}

export interface Decision {
  case_id: string;
  route: RouteDecision;
  confidence: number;
  components: {
    identity: number; ocr: number; authenticity: number;
    rules_complete: number; scam_safety: number;
  };
  missing: string[];
  reason_simple: { en: string; ur: string };
  rule_version: number;
  approval_token?: string | null;
}

export interface CaseItem {
  id: string;
  citizen_id: string;
  citizen_name: string;
  cnic: string;
  phone: string;
  household_size: number;
  monthly_income: number;
  benefit_type: string;
  requested_amount: number;
  status: CaseStatus;
  decision?: Decision | null;
  officer_notes?: string | null;
  disbursement_ref?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewQueueItem {
  case_id: string;
  citizen_name: string;
  cnic: string;
  requested_amount: number;
  confidence: number;
  priority_score: number;
  status: CaseStatus;
  handoff_packet: {
    flags: string[];
    suggested_action: string;
    component_breakdown: Decision["components"];
  };
  submitted_at: string;
}

export interface RuleSet {
  version: number;
  name: string;
  max_monthly_income: number;
  is_active: boolean;
}

export interface SimulationResult {
  total_cases_simulated: number;
  previous_rule_version: number;
  draft_rule_version: number;
  previous_approval_rate: number;
  projected_approval_rate: number;
  approval_rate_delta: number;
  impact_summary: string;
  affected_case_ids: string[];
}

export interface AuditEntry {
  id?: string;
  prev_hash: string;
  current_hash: string;
  timestamp: string;
  actor?: string | null;
  actor_role?: string | null;
  action: string;
  resource_id?: string | null;
  result?: string | null;
}

export interface ChainStatus {
  is_valid: boolean;
  total_records: number;
  corrupted_at_index?: number | null;
  head_hash?: string | null;
}

class RahbarApiClient {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  private getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") return localStorage.getItem("token");
    return null;
  }

  private authHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    if (USE_MOCK) return (await mockRequest(endpoint, options)) as T;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...this.authHeaders(),
      ...((options.headers as Record<string, string>) ?? {}),
    };
    const res = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, { ...options, headers });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw (body?.detail ?? { message_en: `Error ${res.status}` }) as ApiError;
    }
    return res.json() as Promise<T>;
  }

  // ---------- Auth ----------
  async login(username: string, password: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    this.token = data.access_token;
    return data;
  }

  me() {
    return this.request<Record<string, unknown>>("/auth/me");
  }

  // ---------- AI & voice ----------
  async transcribeUrduAudio(audioBlob: Blob): Promise<Record<string, unknown>> {
    if (USE_MOCK) return { text: "میرا نام پروین بی بی ہے", language: "ur", confidence: 0.9 };
    const formData = new FormData();
    formData.append("audio", audioBlob);
    const res = await fetch(`${API_BASE_URL}${API_PREFIX}/ai/voice/stt`, {
      method: "POST",
      headers: this.authHeaders(),
      body: formData,
    });
    return res.json();
  }

  checkScamSms(text: string) {
    return this.request<ScamCheckResponse>("/ai/scam-check", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }

  getEvalSummary() {
    return this.request<Record<string, unknown>>("/ai/eval-summary");
  }

  // ---------- Cases & decisions ----------
  createCase(data: CaseCreate) {
    return this.request<CaseItem>("/cases", { method: "POST", body: JSON.stringify(data) });
  }
  listCases() {
    return this.request<CaseItem[]>("/cases");
  }
  getCase(caseId: string) {
    return this.request<CaseItem>(`/cases/${caseId}`);
  }
  submitCase(caseId: string) {
    return this.request<CaseItem>(`/cases/${caseId}/submit`, { method: "POST" });
  }
  evaluateCase(caseId: string) {
    return this.request<Decision>(`/decisions/evaluate/${caseId}`, { method: "POST" });
  }

  // ---------- Consent ----------
  grantConsent(citizen_id: string, scope: ConsentScope, helper_id?: string) {
    return this.request<Record<string, unknown>>("/consent/grant", {
      method: "POST",
      body: JSON.stringify({ citizen_id, scope, helper_id }),
    });
  }
  withdrawConsent(citizen_id: string, scope: ConsentScope, reason?: string) {
    return this.request<Record<string, unknown>>("/consent/withdraw", {
      method: "POST",
      body: JSON.stringify({ citizen_id, scope, reason }),
    });
  }
  getConsentStatus(citizenId: string) {
    return this.request<ConsentStatus>(`/consent/status/${citizenId}`);
  }

  // ---------- Officer queue ----------
  getOfficerQueue() {
    return this.request<ReviewQueueItem[]>("/review/queue");
  }
  decideReview(caseId: string, decision: string, approved: boolean, mandatory_officer_notes: string) {
    return this.request<Record<string, unknown>>(`/review/${caseId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, approved, mandatory_officer_notes }),
    });
  }

  // ---------- Admin ----------
  getActiveRules() {
    return this.request<RuleSet>("/rules/active");
  }
  publishRule(name: string, rule_set: RuleSet) {
    return this.request<RuleSet>("/rules/publish", {
      method: "POST",
      body: JSON.stringify({ name, rule_set }),
    });
  }
  simulateRules(draft_rule_set: RuleSet, sample_size = 100) {
    return this.request<SimulationResult>("/digital-twin/simulate", {
      method: "POST",
      body: JSON.stringify({ draft_rule_set, sample_size }),
    });
  }

  // ---------- Auditor ----------
  getAuditLogs() {
    return this.request<AuditEntry[]>("/audit/logs");
  }
  verifyAuditChain() {
    return this.request<ChainStatus>("/audit/verify-chain");
  }
}

export const api = new RahbarApiClient();
export const login = (username: string, password: string) => api.login(username, password);
export default api;