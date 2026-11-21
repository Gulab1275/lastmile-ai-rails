import type { Role } from "./api";

export interface Session {
  token: string;
  role: Role;
  userId: string;
  username: string;
}

export function saveSession(s: Session) {
  localStorage.setItem("token", s.token);
  localStorage.setItem("role", s.role);
  localStorage.setItem("user_id", s.userId);
  localStorage.setItem("username", s.username);
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role") as Role | null;
  if (!token || !role) return null;
  return {
    token, role,
    userId: localStorage.getItem("user_id") ?? "",
    username: localStorage.getItem("username") ?? "",
  };
}

export function clearSession() {
  ["token", "role", "user_id", "username", "active_citizen"].forEach((k) => localStorage.removeItem(k));
}

/** The citizen whose data we are acting on. Helpers can switch this (Helper Mode). */
export function getActiveCitizenId(): string {
  return localStorage.getItem("active_citizen") || localStorage.getItem("user_id") || "";
}

/** Menu per role (G3). href = page route. */
export const NAV: Record<Role, { href: string; en: string; ur: string }[]> = {
  citizen: [
    { href: "/dashboard", en: "Home", ur: "ہوم" },
    { href: "/consent", en: "My Data", ur: "میرا ڈیٹا" },
  ],
  helper: [
    { href: "/dashboard", en: "Home", ur: "ہوم" },
    { href: "/consent", en: "Consent", ur: "رضامندی" },
    { href: "/scam", en: "Scam Check", ur: "فراڈ چیک" },
  ],
  officer: [{ href: "/dashboard", en: "Home", ur: "ہوم" }],
  admin: [{ href: "/dashboard", en: "Home", ur: "ہوم" }],
  auditor: [{ href: "/dashboard", en: "Home", ur: "ہوم" }],
};
// Citizens who are shopkeepers also need the scam checker:
NAV.citizen.push({ href: "/scam", en: "Scam Check", ur: "فراڈ چیک" });

/** Read text aloud with the phone's built-in voice (works offline). */
export function speak(text: string, lang: "ur-PK" | "en-US" = "ur-PK") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  window.speechSynthesis.speak(u);
}