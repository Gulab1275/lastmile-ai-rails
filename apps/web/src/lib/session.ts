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
  ["token", "role", "user_id", "username", "active_citizen", "active_citizen_name"].forEach((k) =>
    localStorage.removeItem(k)
  );
}

/** The citizen whose data we are acting on. Helpers switch this (Helper Mode). */
export function getActiveCitizenId(): string {
  return localStorage.getItem("active_citizen") || localStorage.getItem("user_id") || "";
}
export function getActiveCitizenName(): string {
  return localStorage.getItem("active_citizen_name") || "";
}
export function setActiveCitizen(id: string, name: string) {
  localStorage.setItem("active_citizen", id);
  localStorage.setItem("active_citizen_name", name);
}

/** Menu per role (G3). */
type NavItem = { href: string; en: string; ur: string };
const HOME: NavItem = { href: "/dashboard", en: "Home", ur: "ہوم" };
const SCAM: NavItem = { href: "/scam", en: "Scam Check", ur: "فراڈ چیک" };
const EVAL: NavItem = { href: "/eval", en: "AI Report", ur: "اے آئی رپورٹ" };

export const NAV: Record<Role, NavItem[]> = {
  citizen: [
    HOME,
    { href: "/apply", en: "Apply", ur: "درخواست" },
    { href: "/cases", en: "My Cases", ur: "میرے کیس" },
    { href: "/consent", en: "My Data", ur: "میرا ڈیٹا" },
    SCAM,
  ],
  helper: [
    HOME,
    { href: "/families", en: "Families", ur: "خاندان" },
    { href: "/apply", en: "Apply", ur: "درخواست" },
    { href: "/cases", en: "Cases", ur: "کیس" },
    { href: "/consent", en: "Consent", ur: "رضامندی" },
    SCAM,
  ],
  officer: [HOME, { href: "/officer", en: "Review Queue", ur: "ریویو قطار" }, EVAL],
  admin: [HOME, { href: "/admin", en: "Rules", ur: "قواعد" }, EVAL],
  auditor: [HOME, { href: "/auditor", en: "Audit Log", ur: "آڈٹ لاگ" }, EVAL],
};

/** Read text aloud with the phone's built-in voice (works offline). */
export function speak(text: string, lang: "ur-PK" | "en-US" = "ur-PK") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang;
  window.speechSynthesis.speak(u);
}