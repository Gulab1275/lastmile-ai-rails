/**
 * Rahbar API client (Next.js / PWA).
 * Endpoints match docs/openapi.json.
 */

// Base URL WITHOUT /api/v1 (the prefix is added below)
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

export type Role = "citizen" | "helper" | "officer" | "admin" | "auditor";

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
  label?: string;
  confidence?: number;
  reasons?: string[];
  [key: string]: unknown;
}

export type ConsentScope = string; // use the scope names from the API docs

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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...this.authHeaders(),
      ...((options.headers as Record<string, string>) ?? {}),
    };

    const res = await fetch(`${API_BASE_URL}${API_PREFIX}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw (body?.detail ?? {
        message_en: `Error ${res.status}`,
      }) as ApiError;
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

  // ---------- Cases & decisions ----------
  createCase(data: CaseCreate) {
    return this.request<Record<string, unknown>>("/cases", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listCases() {
    return this.request<unknown[]>("/cases");
  }

  getCase(caseId: string) {
    return this.request<Record<string, unknown>>(`/cases/${caseId}`);
  }

  evaluateCase(caseId: string) {
    return this.request<Record<string, unknown>>(
      `/decisions/evaluate/${caseId}`,
      { method: "POST" }
    );
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
    return this.request<Record<string, unknown>>(
      `/consent/status/${citizenId}`
    );
  }

  // ---------- Officer queue ----------
  getOfficerQueue() {
    return this.request<unknown[]>("/review/queue");
  }

  decideReview(
    caseId: string,
    decision: string,
    approved: boolean,
    mandatory_officer_notes: string
  ) {
    return this.request<Record<string, unknown>>(
      `/review/${caseId}/decision`,
      {
        method: "POST",
        body: JSON.stringify({ decision, approved, mandatory_officer_notes }),
      }
    );
  }

  // ---------- Admin ----------
  getActiveRules() {
    return this.request<Record<string, unknown>>("/rules/active");
  }

  simulateRules(draft_rule_set: Record<string, unknown>, sample_size = 100) {
    return this.request<Record<string, unknown>>("/digital-twin/simulate", {
      method: "POST",
      body: JSON.stringify({ draft_rule_set, sample_size }),
    });
  }

  // ---------- Auditor ----------
  getAuditLogs() {
    return this.request<unknown>("/audit/logs");
  }

  verifyAuditChain() {
    return this.request<Record<string, unknown>>("/audit/verify-chain");
  }
}

export const api = new RahbarApiClient();
export const login = (username: string, password: string) =>
  api.login(username, password);
export default api;