import api, { type Role } from "./api";

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
const MAP: NavItem = { href: "/scam-map", en: "Scam Map", ur: "فراڈ نقشہ" };
const DOCS: NavItem = { href: "/documents", en: "Check Document", ur: "کاغذ جانچ" };
const IDCHK: NavItem = { href: "/identity", en: "ID Check", ur: "شناخت جانچ" };

export const NAV: Record<Role, NavItem[]> = {
  citizen: [
    HOME,
    { href: "/apply", en: "Apply", ur: "درخواست" },
    { href: "/cases", en: "My Cases", ur: "میرے کیس" },
    { href: "/consent", en: "My Data", ur: "میرا ڈیٹا" },
    SCAM,
    DOCS,
    MAP,
  ],
  helper: [
    HOME,
    { href: "/families", en: "Families", ur: "خاندان" },
    { href: "/apply", en: "Apply", ur: "درخواست" },
    { href: "/cases", en: "Cases", ur: "کیس" },
    { href: "/consent", en: "Consent", ur: "رضامندی" },
    SCAM,
    DOCS,
    IDCHK,
    MAP,
  ],
  officer: [HOME, { href: "/officer", en: "Review Queue", ur: "ریویو قطار" }, IDCHK, DOCS, MAP, EVAL],
  admin: [HOME, { href: "/admin", en: "Rules & API Keys", ur: "قواعد و چابیاں" }, EVAL, MAP],
  auditor: [HOME, { href: "/auditor", en: "Audit Log", ur: "آڈٹ لاگ" }, EVAL],
};

let currentAudio: HTMLAudioElement | null = null;

/**
 * Read text aloud with server TTS first (under 3s), falling back to browser speechSynthesis.
 * Cached per text and language. Never blocks user actions.
 */
export async function speak(text: string, lang: "ur-PK" | "en-US" = "ur-PK") {
  if (typeof window === "undefined" || !text.trim()) return;

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }

  try {
    const isUrdu = lang.startsWith("ur");
    const blob = await api.synthesizeSpeech(text, isUrdu ? "ur" : "en");
    if (blob) {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudio = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        if (currentAudio === audio) currentAudio = null;
      };
      await audio.play();
      return;
    }
  } catch {
    // fallback below
  }

  if ("speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    const voices = window.speechSynthesis.getVoices();
    const urduVoice = voices.find((v) => v.lang.startsWith("ur"));
    if (urduVoice) {
      u.voice = urduVoice;
    }
    window.speechSynthesis.speak(u);
  }
}
