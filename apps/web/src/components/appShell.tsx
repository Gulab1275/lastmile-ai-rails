"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, UserRound, Zap, Languages, Home, FilePlus, Folder, Shield, AlertTriangle } from "lucide-react";
import { NAV, clearSession, getActiveCitizenName, getSession, type Session } from "@/lib/session";
import { NAV_ICONS } from "@/lib/navIcons";
import { flushQueue, queuedCount } from "@/lib/offlineQueue";
import { useUI } from "@/lib/uiContext";
import Logo from "@/components/logo";

const ROLE_LABEL: Record<string, { ur: string; en: string }> = {
  citizen: { ur: "شہری", en: "Citizen" },
  helper: { ur: "مددگار ورکر", en: "Field Helper" },
  officer: { ur: "ریلیف افسر", en: "Relief Officer" },
  admin: { ur: "پالیسی ایڈمن", en: "Policy Admin" },
  auditor: { ur: "آڈیٹر", en: "Auditor" },
};

const ROLE_THEMES: Record<string, { bg: string; border: string; activeNav: string; text: string }> = {
  citizen: {
    bg: "bg-gradient-to-br from-[#0B4F43] via-[#0F6B5A] to-[#0B4F43]",
    border: "border-[#1F8A5B]",
    activeNav: "bg-[#0B4F43] text-white shadow-lift",
    text: "text-[#0B4F43]",
  },
  helper: {
    bg: "bg-gradient-to-br from-[#0369A1] via-[#0284C7] to-[#0369A1]",
    border: "border-[#0284C7]",
    activeNav: "bg-[#0284C7] text-white shadow-lift",
    text: "text-[#0284C7]",
  },
  officer: {
    bg: "bg-gradient-to-br from-[#3730A3] via-[#4C5FD5] to-[#3730A3]",
    border: "border-[#4C5FD5]",
    activeNav: "bg-[#4C5FD5] text-white shadow-lift",
    text: "text-[#4C5FD5]",
  },
  admin: {
    bg: "bg-gradient-to-br from-[#B45309] via-[#D97706] to-[#92400E]",
    border: "border-[#D97706]",
    activeNav: "bg-[#D97706] text-white shadow-lift",
    text: "text-[#D97706]",
  },
  auditor: {
    bg: "bg-gradient-to-br from-[#334155] via-[#475569] to-[#1E293B]",
    border: "border-[#475569]",
    activeNav: "bg-[#475569] text-white shadow-lift",
    text: "text-[#475569]",
  },
};

export default function AppShell({ children, title }: { children: React.ReactNode; title?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const { lang, toggleLang, lowBandwidth, toggleLowBandwidth, t } = useUI();
  const [session, setSession] = useState<Session | null>(null);
  const [online, setOnline] = useState(true);
  const [pending, setPending] = useState(0);
  const [syncMsg, setSyncMsg] = useState("");
  const [acting, setActing] = useState("");

  const sync = useCallback(async (userId: string) => {
    try {
      const n = await flushQueue(userId);
      if (n > 0) {
        setSyncMsg(`${n} آف لائن فارم بھیج دیے گئے · ${n} offline form(s) synced`);
        setTimeout(() => setSyncMsg(""), 6000);
      }
    } catch {
      /* will retry on next reconnect */
    }
    setPending(await queuedCount());
  }, []);

  useEffect(() => {
    const s = getSession();
    if (!s) {
      router.replace("/");
      return;
    }
    setSession(s);
    setActing(getActiveCitizenName());
    setOnline(navigator.onLine);
    queuedCount().then(setPending);
    if (navigator.onLine) sync(s.userId);
    const up = () => { setOnline(true); sync(s.userId); };
    const down = () => setOnline(false);
    const onCitizenChanged = () => setActing(getActiveCitizenName());

    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    window.addEventListener("active_citizen_changed", onCitizenChanged);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
      window.removeEventListener("active_citizen_changed", onCitizenChanged);
    };
  }, [router, sync]);

  if (!session) return null;

  const initials = session.username.split("_").map((p) => p[0]?.toUpperCase()).join("").slice(0, 2);
  const roleTheme = ROLE_THEMES[session.role] || ROLE_THEMES.citizen;
  const isCitizenPath = session.role === "citizen" || session.role === "helper";

  return (
    <div className="min-h-screen bg-[#F7F4EE] text-[#17302B] flex flex-col">
      {/* ---------- Top Header with Role Tint ---------- */}
      <header className={`relative overflow-hidden ${roleTheme.bg} text-white rounded-b-[2rem] shadow-lift transition-colors duration-300`}>
        <div className="pattern-dots absolute inset-0 opacity-30" aria-hidden="true" />
        <div className="relative max-w-3xl mx-auto px-4 pt-3.5 pb-3 flex items-center justify-between gap-2">
          {/* Logo & Platform Name */}
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <Logo size={40} />
            <div>
              <p className="text-2xl font-bold font-heading leading-none">رہبر · Rahbar</p>
              <p className="text-[11px] text-[#DDEFE9] opacity-90 truncate">AI on Public Rails · Coder&apos;s Cup &apos;26</p>
            </div>
          </Link>

          {/* Quick Header Toggles: Language, Low-Bandwidth, Network & Logout */}
          <div className="flex items-center gap-1.5">
            {/* Language Switcher */}
            <button
              onClick={toggleLang}
              className="min-h-[40px] px-2.5 rounded-xl bg-white/15 hover:bg-white/25 text-xs font-bold flex items-center gap-1 transition"
              title="Toggle Urdu / English"
              type="button"
            >
              <Languages className="w-3.5 h-3.5 text-[#E8A33D]" />
              <span>{lang === "ur" ? "English" : "اردو"}</span>
            </button>

            {/* Low-Bandwidth Mode */}
            <button
              onClick={toggleLowBandwidth}
              className={`min-h-[40px] px-2 rounded-xl text-xs font-bold flex items-center gap-1 transition ${
                lowBandwidth ? "bg-[#E8A33D] text-[#17302B]" : "bg-white/15 hover:bg-white/25 text-white"
              }`}
              title="Toggle Low-Bandwidth Mode"
              type="button"
            >
              <Zap className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{lowBandwidth ? "Low-Net ON" : "Fast-Net"}</span>
            </button>

            {/* Online Indicator */}
            <span className="flex items-center gap-1 bg-white/15 rounded-xl px-2 py-1 text-[11px] font-bold">
              <span className={`w-2 h-2 rounded-full ${online ? "bg-[#34D399] animate-pulse-stone" : "bg-[#E8A33D]"}`} />
              <span className="hidden sm:inline">{online ? "Online" : "Offline"}</span>
            </span>

            {/* Logout */}
            <button
              onClick={() => { clearSession(); router.replace("/"); }}
              className="min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl bg-white/15 hover:bg-white/25 transition"
              aria-label="Logout"
              type="button"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* User Identity Strip */}
        <div className="relative max-w-3xl mx-auto px-4 pb-3 flex items-center justify-between border-t border-white/10 pt-2 text-xs">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-full bg-[#E8A33D] text-[#17302B] font-bold flex items-center justify-center shadow-sm text-xs">
              {initials}
            </div>
            <div className="leading-tight">
              <p className="font-bold text-sm">{session.username}</p>
              <p className="text-[10px] text-[#DDEFE9]">
                {ROLE_LABEL[session.role]?.ur} · {ROLE_LABEL[session.role]?.en}
              </p>
            </div>
          </div>
          {session.role === "helper" && acting && (
            <span className="bg-[#FEF3C7] text-[#92400E] px-2.5 py-1 rounded-full font-bold text-[11px] flex items-center gap-1">
              <UserRound className="w-3 h-3" /> {acting}
            </span>
          )}
        </div>
      </header>

      {/* ---------- Desktop & Tablet Navigation Menu ---------- */}
      <nav className="sticky top-0 z-30 bg-[#F7F4EE]/95 backdrop-blur border-b border-[#E2DDD3] shadow-sm">
        <div className="max-w-3xl mx-auto px-3 py-2 flex gap-2 overflow-x-auto scrollbar-none">
          {NAV[session.role].map((item) => {
            const Icon = NAV_ICONS[item.href];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`min-h-[44px] px-3.5 flex items-center gap-2 rounded-2xl whitespace-nowrap font-bold text-xs sm:text-sm transition ${
                  active
                    ? roleTheme.activeNav
                    : "bg-white text-[#17302B] hover:bg-[#DDEFE9]/60 border border-[#E2DDD3]"
                }`}
              >
                {Icon && <Icon className="w-4 h-4" />}
                <span>{item.ur}</span>
                <span className="text-[11px] opacity-75 font-normal">· {item.en}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* ---------- Status Strips (Offline & Sync Notifications) ---------- */}
      {!online && (
        <div className="bg-[#FEF3C7] text-[#92400E] border-b border-[#FCD34D] text-center py-2 px-3 font-bold text-xs">
          انٹرنیٹ بند ہے · Offline mode active — claims saved locally on your phone
        </div>
      )}
      {pending > 0 && (
        <div className="bg-[#E0F2FE] text-[#075985] text-center py-2 px-3 font-bold text-xs">
          {pending} فارم بھیجنے کے منتظر · {pending} form(s) waiting to sync
        </div>
      )}
      {syncMsg && <div className="bg-[#D1FAE5] text-[#065F46] text-center py-2 px-3 font-bold text-xs">{syncMsg}</div>}

      {/* ---------- Main Page Content ---------- */}
      <main
        className={`flex-1 max-w-3xl w-full mx-auto p-4 pb-24 sm:pb-16 space-y-4 stagger ${
          isCitizenPath ? "text-[18px]" : "text-[16px]"
        }`}
      >
        {title && (
          <h1 className="text-2xl font-bold font-heading text-[#0B4F43] tracking-tight">
            {title}
          </h1>
        )}
        {children}
      </main>

      {/* ---------- Mobile Bottom Bar for Citizen Routes ---------- */}
      {isCitizenPath && (
        <div className="fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur border-t border-[#E2DDD3] z-40 sm:hidden flex justify-around py-1.5 px-2 shadow-lift">
          <Link
            href="/dashboard"
            className={`flex flex-col items-center justify-center p-1 rounded-xl text-xs font-bold ${
              pathname === "/dashboard" ? "text-[#0B4F43]" : "text-[#5B6F6A]"
            }`}
          >
            <Home className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">ہوم</span>
          </Link>
          <Link
            href="/apply"
            className={`flex flex-col items-center justify-center p-1 rounded-xl text-xs font-bold ${
              pathname === "/apply" ? "text-[#0B4F43]" : "text-[#5B6F6A]"
            }`}
          >
            <FilePlus className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">درخواست</span>
          </Link>
          <Link
            href="/cases"
            className={`flex flex-col items-center justify-center p-1 rounded-xl text-xs font-bold ${
              pathname === "/cases" ? "text-[#0B4F43]" : "text-[#5B6F6A]"
            }`}
          >
            <Folder className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">کیس</span>
          </Link>
          <Link
            href="/consent"
            className={`flex flex-col items-center justify-center p-1 rounded-xl text-xs font-bold ${
              pathname === "/consent" ? "text-[#0B4F43]" : "text-[#5B6F6A]"
            }`}
          >
            <Shield className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">ڈیٹا</span>
          </Link>
          <Link
            href="/scam"
            className={`flex flex-col items-center justify-center p-1 rounded-xl text-xs font-bold ${
              pathname === "/scam" ? "text-[#0B4F43]" : "text-[#5B6F6A]"
            }`}
          >
            <AlertTriangle className="w-5 h-5" />
            <span className="text-[10px] mt-0.5">فراڈ چیک</span>
          </Link>
        </div>
      )}

      {/* ---------- Footer ---------- */}
      <footer className="text-center text-xs text-[#5B6F6A] pb-8 pt-2">
        <p>رہبر (Rahbar) · The Last Mile: AI on Public Rails · Coder&apos;s Cup &apos;26</p>
      </footer>
    </div>
  );
}
