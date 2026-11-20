/**
 * Rahbar API Client for Frontend (Next.js / PWA).
 * Provides typed methods for all 5 roles:
 * - Citizen (Voice intake, OCR blur, form submission)
 * - Helper (40-family selector, granular consent management)
 * - Shopkeeper (SMS scam verification, fraud heatmap)
 * - Officer (Triage review queue, token-gated approval)
 * - Admin (Digital twin simulations, rules publishing)
 * - Auditor (SHA-256 cryptographic audit chain)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export interface CitizenClaimRequest {
  citizen_name: string;
  cnic: string;
  family_members_count: number;
  monthly_income_pkr: number;
  requested_amount_pkr: number;
  documents: Array<{ doc_type: string; file_url: string; qr_code_valid?: boolean }>;
}

export interface DecisionResult {
  case_id: string;
  verdict: 'auto_approve' | 'ask_more_proof' | 'human_review';
  weakest_link_score: number;
  p_wrong: number;
  reason: string;
  payment_status?: string;
  raast_reference?: string;
}

export interface ScamCheckRequest {
  text: string;
  phone_number?: string;
  region?: string;
}

export interface ScamCheckResponse {
  label: 'scam' | 'legitimate';
  confidence: number;
  reasons: string[];
}

export interface ConsentScopeUpdate {
  citizen_id: string;
  scope: 'identity' | 'income' | 'bills' | 'helper_acting';
  granted: boolean;
}

class RahbarApiClient {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers as Record<string, string> || {}),
    };

    const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;
    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`API Error [${response.status}]: ${errorBody}`);
    }

    return response.json();
  }

  // AI & Voice Services
  async transcribeUrduAudio(audioBlob: Blob): Promise<{ transcript: string; confidence: number }> {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    const headers = this.token ? { Authorization: `Bearer ${this.token}` } : {};
    const res = await fetch(`${API_BASE_URL}${API_PREFIX}/ai/transcribe`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return res.json();
  }

  async checkScamSms(payload: ScamCheckRequest): Promise<ScamCheckResponse> {
    return this.request<ScamCheckResponse>('/ai/scam-check', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Decision & Case Services
  async evaluateClaim(claim: CitizenClaimRequest): Promise<DecisionResult> {
    return this.request<DecisionResult>('/decision/evaluate', {
      method: 'POST',
      body: JSON.stringify(claim),
    });
  }

  // Consent Gateway
  async updateConsent(update: ConsentScopeUpdate): Promise<{ status: string; updated_scope: string }> {
    return this.request('/consent/update', {
      method: 'POST',
      body: JSON.stringify(update),
    });
  }

  async getCitizenConsents(citizenId: string): Promise<Record<string, { granted: boolean }>> {
    return this.request(`/consent/status/${citizenId}`);
  }

  // Officer Queue
  async getOfficerQueue(): Promise<any[]> {
    return this.request('/review/queue');
  }

  async decideOfficerReview(caseId: string, action: 'approve' | 'reject', notes: string): Promise<any> {
    return this.request(`/review/${caseId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    });
  }

  // Digital Twin Simulation
  async runDigitalTwinSimulation(policyDraft: { max_income: number; max_auto_payout: number }): Promise<any> {
    return this.request('/digital-twin/simulate', {
      method: 'POST',
      body: JSON.stringify(policyDraft),
    });
  }

  // Cryptographic Audit Hash Chain
  async getAuditLedger(limit: number = 20): Promise<any> {
    return this.request(`/audit/chain?limit=${limit}`);
  }

  async verifyAuditChainIntegrity(): Promise<{ verified: boolean; length: number; errors: string[] }> {
    return this.request('/audit/verify');
  }
}

export const api = new RahbarApiClient();
export default api;
