import { mockRequest } from "./mock";

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
  code?: string;
  status?: number;
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
  min_household_size: number;
  max_auto_approve_amount: number;
  requires_valid_cnic: boolean;
  requires_utility_bill: boolean;
  max_wrong_prob_auto_approve: number;
  max_wrong_prob_ask_proof: number;
  is_active: boolean;
}

export interface RuleVersion {
  version: number;
  name: string;
  is_active: boolean;
  rule_set: RuleSet;
  created_at: string;
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

export interface Family {
  id: string;
  name: string;
  cnic: string;
}

export interface ExtractedForm {
  full_name?: string | null;
  cnic?: string | null;
  phone?: string | null;
  household_size?: number | null;
  monthly_income?: number | null;
  missing_fields: string[];
  confidence: number;
}

export interface SweepPoint {
  threshold: number;
  auto_approve_count: number;
  wrong_approvals: number;
  human_reviews: number;
  ask_proofs: number;
  expected_cost_per_case: number;
}

export interface EvalSummary {
  total_test_samples: number;
  scam_classifier_metrics: {
    accuracy: number; precision: number; recall: number; f1_score: number;
    false_alarm_rate: number; confusion_matrix: Record<string, number>;
  };
  identity_matcher_metrics: Record<string, number>;
  decision_engine_metrics: {
    optimal_p_wrong_threshold: number; min_expected_cost_per_case: number;
    auto_approve_rate: string; human_review_rate: string; ask_more_proof_rate: string;
    auto_reject_rate: number;
  };
  threshold_sweep_curve: SweepPoint[];
  system_guarantees: { guarantee: string; verified: boolean; detail: string }[];
}

export interface SyncResult {
  batch_id?: string;
  [key: string]: unknown;
}
export interface NadraResult {
  matched: boolean;
  match_score: number;
  canonical_cnic: string;
  canonical_name: string;
  deceased: boolean;
  status: string;
  latency_ms: number;
}

export interface DocCheck {
  fields: Record<string, unknown>;
  field_confidences: Record<string, number>;
  blur_score: number;
  is_blurry: boolean;
  tamper_score: number;
  qr_verified?: boolean | null;
}

export interface Hotspot {
  district: string;
  latitude: number;
  longitude: number;
  incident_count: number;
  threat_intensity: number;
  threat_level: "CRITICAL" | "HIGH" | "MODERATE";
  primary_scam_type: string;
}

export interface ScamMap {
  total_active_clusters: number;
  total_analyzed_threats: number;
  category_distribution: Record<string, number>;
  hotspots: Hotspot[];
  top_keywords: { keyword_ur: string; keyword_en: string; frequency: number; category: string }[];
  temporal_trends: { date: string; blocked_scams: number; shopkeeper_reports: number }[];
  summary: {
    highest_risk_district: string;
    dominant_scam_category: string;
    citizen_protection_advice_ur: string;
    citizen_protection_advice_en: string;
  };
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
      const d = body?.detail;
      const detail =
        typeof d === "string" ? { message_en: d }
        : Array.isArray(d) ? { message_en: "Some information is missing or invalid" }
        : d ?? { message_en: `Error ${res.status}` };
      throw { ...detail, status: res.status } as ApiError;
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
    return this.request<EvalSummary>("/ai/eval-summary");
  }
  extractForm(text: string) {
    return this.request<ExtractedForm>("/ai/extract-form", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  }
  syncOfflineBatch(helper_id: string, batch_id: string, queued_cases: Record<string, unknown>[]) {
    return this.request<SyncResult>("/ai/sync-offline-batch", {
      method: "POST",
      body: JSON.stringify({ helper_id, batch_id, queued_cases, client_timestamp: new Date().toISOString() }),
    });
  }

    verifyIdentity(cnic: string, full_name: string, chaos?: string) {
    const q = chaos && chaos !== "none" ? `?chaos=${chaos}` : "";
    return this.request<NadraResult>(`/mock/identity/verify${q}`, {
      method: "POST",
      body: JSON.stringify({ cnic, full_name }),
    });
  }
  async checkDocument(file: File): Promise<DocCheck> {
    if (USE_MOCK) {
      return mockRequest("/ai/ocr", { method: "POST", body: JSON.stringify({ file_name: file.name }) }) as Promise<DocCheck>;
    }
    const form = new FormData();
    form.append("files", file);
    const res = await fetch(`${API_BASE_URL}${API_PREFIX}/ai/ocr`, {
      method: "POST",
      headers: this.authHeaders(),
      body: form,
    });
    if (!res.ok) throw { message_en: `Document check failed (${res.status})`, status: res.status } as ApiError;
    return res.json();
  }
  getScamMap() {
    return this.request<ScamMap>("/ai/scam-map");
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
  uploadDocument(caseId: string, file: File, docType = "utility_bill") {
    // The backend attaches a document record (JSON), not the raw file.
    return this.request<CaseItem>(`/cases/${caseId}/documents`, {
      method: "POST",
      body: JSON.stringify({
        doc_id: `doc-${Date.now()}`,
        doc_type: docType,
        file_name: file.name,
        file_url: `local://${file.name}`,
      }),
    });
  }
  explainCase(caseId: string, view: "citizen" | "auditor") {
    return this.request<Record<string, unknown>>(`/decisions/explain/${caseId}?view=${view}`);
  }
  evaluateCase(caseId: string) {
    return this.request<Decision>(`/decisions/evaluate/${caseId}`, { method: "POST" });
  }

  // ---------- Helper Mode ----------
  async getFamilies(): Promise<Family[]> {
    if (USE_MOCK) return mockRequest("/helper/families") as Promise<Family[]>;
    const cases = await this.listCases();
    const seen = new Map<string, Family>();
    cases.forEach((c) => seen.set(c.citizen_id, { id: c.citizen_id, name: c.citizen_name, cnic: c.cnic }));
    return Array.from(seen.values());
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
  listRuleVersions() {
    return this.request<RuleVersion[]>("/rules/versions");
  }
  publishRule(rule_set: RuleSet) {
    // The backend expects the RuleSet itself as the request body.
    return this.request<RuleSet>("/rules/publish", {
      method: "POST",
      body: JSON.stringify(rule_set),
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