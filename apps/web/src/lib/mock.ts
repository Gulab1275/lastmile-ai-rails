import type { Role, TokenResponse } from "./api";

const USERS: Record<string, Role> = {
  citizen_parveen: "citizen",
  citizen_tariq: "citizen",
  helper_shazia: "helper",
  officer_aslam: "officer",
  admin_ayesha: "admin",
  auditor_iqbal: "auditor",
};

export async function mockRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<unknown> {
  await new Promise((r) => setTimeout(r, 300));

  if (endpoint === "/auth/login") {
    const { username, password } = JSON.parse(String(options.body ?? "{}"));
    const role = USERS[username];
    if (!role || password !== "password123") {
      throw {
        message_en: "Wrong username or password",
        message_ur: "صارف کا نام یا پاس ورڈ غلط ہے",
      };
    }
    const result: TokenResponse = {
      access_token: `mock-token-${username}`,
      refresh_token: "mock-refresh",
      role,
      user_id: `mock-${username}`,
      username,
    };
    return result;
  }

  throw { message_en: `No mock data yet for ${endpoint}` };
}