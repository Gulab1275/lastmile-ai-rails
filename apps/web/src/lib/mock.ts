import type { Role, TokenResponse } from "./api";

const USERS: Record<string, Role> = {
  citizen_parveen: "citizen",
  citizen_tariq: "citizen",
  helper_shazia: "helper",
  officer_aslam: "officer",
  admin_ayesha: "admin",
  auditor_iqbal: "auditor",
};

type Entry = {
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
  helper_id: string | null;
};

// In-memory fake database (resets when you reload the page)
const consents: Record<string, Record<string, Entry>> = {};

function ensure(citizenId: string) {
  if (!consents[citizenId]) {
    const now = new Date().toISOString();
    consents[citizenId] = {
      identity: { granted: true, granted_at: now, revoked_at: null, helper_id: null },
      income: { granted: true, granted_at: now, revoked_at: null, helper_id: null },
    };
  }
  return consents[citizenId];
}

export async function mockRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<unknown> {
  await new Promise((r) => setTimeout(r, 300));
  const body = JSON.parse(String(options.body ?? "{}"));

  if (endpoint === "/auth/login") {
    const role = USERS[body.username];
    if (!role || body.password !== "password123") {
      throw {
        message_en: "Wrong username or password",
        message_ur: "صارف کا نام یا پاس ورڈ غلط ہے",
      };
    }
    const result: TokenResponse = {
      access_token: `mock-token-${body.username}`,
      refresh_token: "mock-refresh",
      role,
      user_id: `mock-${body.username}`,
      username: body.username,
    };
    return result;
  }

  if (endpoint.startsWith("/consent/status/")) {
    const id = endpoint.split("/").pop() as string;
    return { citizen_id: id, consents: ensure(id) };
  }

  if (endpoint === "/consent/grant") {
    const map = ensure(body.citizen_id);
    map[body.scope] = {
      granted: true,
      granted_at: new Date().toISOString(),
      revoked_at: null,
      helper_id: body.helper_id ?? null,
    };
    return { citizen_id: body.citizen_id, scope: body.scope, granted: true };
  }

  if (endpoint === "/consent/withdraw") {
    const map = ensure(body.citizen_id);
    map[body.scope] = {
      granted: false,
      granted_at: map[body.scope]?.granted_at ?? null,
      revoked_at: new Date().toISOString(),
      helper_id: null,
    };
    return { citizen_id: body.citizen_id, scope: body.scope, granted: false };
  }

  throw { message_en: `No mock data yet for ${endpoint}` };
}