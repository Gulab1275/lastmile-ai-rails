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
  citizen: { ur: "شہری سائل", en: "Citizen" },
  helper: { ur: "فیلڈ ورکر / مددگار", en: "Field Helper" },
  officer: { ur: "ریلیف افسر", en: "Relief Officer" },
  admin: { ur: "پالیسی ایڈمن", en: "Policy Admin" },
  auditor: { ur: "آڈیٹر", en: "Auditor" },
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
      /* retry on next network change */
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
  const isCitizenPath = session.role === "citizen" || session.role === "helper";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* ---------- Top Header Bar ---------- */}
      <header className="bg-[#0B4F43] text-white shadow-md border-b border-[#083e34]">
        <div className="max-w-4xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          {/* Logo & Platform Name */}
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="p-1 rounded-xl bg-white/10 group-hover:bg-white/20 transition">
              <Logo size={36} />
            </div>
            <div>
              <p className="text-xl font-bold font-heading leading-tight tracking-tight">
                رہبر <span className="text-sm font-normal text-emerald-200">· Rahbar</span>
              </p>
              <p className="text-[11px] text-emerald-100/80">AI on Public Rails · Digital Relief</p>
            </div>
          </Link>

          {/* Header Action Controls */}
          <div className="flex items-center gap-2">
            {/* Language Switcher */}
            <button
              onClick={toggleLang}
              className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-semibold flex items-center gap-1.5 transition text-emerald-50 border border-white/15"
              title="Toggle Urdu / English"
              type="button"
            >
              <Languages className="w-3.5 h-3.5 text-[#F59E0B]" />
              <span>{lang === "ur" ? "English" : "اردو"}</span>
            </button>

            {/* Low-Bandwidth Mode */}
            <button
              onClick={toggleLowBandwidth}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition border ${lowBandwidth
                ? "bg-[#D97706] text-white border-[#D97706]"
                : "bg-white/10 hover:bg-white/20 text-emerald-50 border-white/15"
                }`}
              title="Toggle Low-Bandwidth Mode"
              type="button"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>{lowBandwidth ? "Low-Net" : "Fast-Net"}</span>
            </button>

            {/* Online Status Pill */}
            <span className="flex items-center gap-1.5 bg-white/10 rounded-lg px-2.5 py-1.5 text-xs text-emerald-50 border border-white/15 font-mono">
              <span className={`w-2 h-2 rounded-full ${online ? "bg-emerald-400" : "bg-amber-400"}`} />
              <span className="hidden md:inline">{online ? "Online" : "Offline"}</span>
            </span>

            {/* Logout */}
            <button
              onClick={() => { clearSession(); router.replace("/"); }}
              className="p-2 flex items-center justify-center rounded-lg bg-white/10 hover:bg-rose-600/80 transition border border-white/15"
              aria-label="Logout"
              title="Sign Out"
              type="button"
            >
              <LogOut className="w-4 h-4 text-emerald-50" />
            </button>
          </div>
        </div>

        {/* User Role Strip */}
        <div className="bg-[#084137] border-t border-white/10">
          <div className="max-w-4xl mx-auto px-4 py-2 flex items-center justify-between text-xs text-emerald-100">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-[#D97706] text-white font-bold flex items-center justify-center text-[10px]">
                {initials}
              </span>
              <span className="font-semibold text-white">{session.username}</span>
              <span className="text-emerald-300">({ROLE_LABEL[session.role]?.ur})</span>
            </div>

            {session.role === "helper" && acting && (
              <span className="bg-amber-400 text-slate-900 px-2.5 py-0.5 rounded-md font-bold text-xs flex items-center gap-1">
                <UserRound className="w-3 h-3" />
                <span>خاندان: {acting}</span>
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ---------- Horizontal Navigation Pill Menu ---------- */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-2 flex gap-2 overflow-x-auto scrollbar-none">
          {NAV[session.role].map((item) => {
            const Icon = NAV_ICONS[item.href];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3.5 py-2 flex items-center gap-2 rounded-xl whitespace-nowrap text-xs font-semibold transition ${active
                  ? "bg-[#0B4F43] text-white shadow-sm"
                  : "text-slate-700 hover:bg-slate-100 border border-transparent hover:border-slate-200"
                  }`}
              >
                {Icon && <Icon className="w-4 h-4 shrink-0" />}
                <span>{item.ur}</span>
                <span className="text-[11px] opacity-75 font-normal">({item.en})</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* ---------- System Notification Banners ---------- */}
      {!online && (
        <div className="bg-amber-50 text-amber-900 border-b border-amber-200 text-center py-2 px-4 text-xs font-medium">
          انٹرنیٹ رابطہ منقطع ہے · Offline mode active — your claims are stored locally and will sync when online.
        </div>
      )}
      {pending > 0 && (
        <div className="bg-sky-50 text-sky-900 border-b border-sky-200 text-center py-2 px-4 text-xs font-medium">
          {pending} درخواستیں بھیجے جانے کی منتظر ہیں · {pending} form(s) waiting to sync
        </div>
      )}
      {syncMsg && (
        <div className="bg-emerald-50 text-emerald-900 border-b border-emerald-200 text-center py-2 px-4 text-xs font-medium">
          {syncMsg}
        </div>
      )}

      {/* ---------- Main Content Viewport ---------- */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 pb-28 sm:pb-16 space-y-5">
        {title && (
          <div className="pb-1">
            <h1 className="text-2xl font-bold font-heading text-slate-900 tracking-tight">
              {title}
            </h1>
          </div>
        )}
        {children}
      </main>

      {/* ---------- Mobile Bottom Bar for Citizen / Helper Paths ---------- */}
      {isCitizenPath && (
        <div className="fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur border-t border-slate-200 z-40 sm:hidden flex justify-around py-2 px-3 shadow-lg">
          <Link
            href="/dashboard"
            className={`flex flex-col items-center justify-center p-1 rounded-lg text-xs font-medium ${pathname === "/dashboard" ? "text-[#0B4F43] font-bold" : "text-slate-600"
              }`}
          >
            <Home className="w-5 h-5 mb-0.5" />
            <span className="text-[10px]">ہوم</span>
          </Link>
          <Link
            href="/apply"
            className={`flex flex-col items-center justify-center p-1 rounded-lg text-xs font-medium ${pathname === "/apply" ? "text-[#0B4F43] font-bold" : "text-slate-600"
              }`}
          >
            <FilePlus className="w-5 h-5 mb-0.5" />
            <span className="text-[10px]">درخواست</span>
          </Link>
          <Link
            href="/cases"
            className={`flex flex-col items-center justify-center p-1 rounded-lg text-xs font-medium ${pathname === "/cases" ? "text-[#0B4F43] font-bold" : "text-slate-600"
              }`}
          >
            <Folder className="w-5 h-5 mb-0.5" />
            <span className="text-[10px]">کیس</span>
          </Link>
          <Link
            href="/consent"
            className={`flex flex-col items-center justify-center p-1 rounded-lg text-xs font-medium ${pathname === "/consent" ? "text-[#0B4F43] font-bold" : "text-slate-600"
              }`}
          >
            <Shield className="w-5 h-5 mb-0.5" />
            <span className="text-[10px]">ڈیٹا</span>
          </Link>
          <Link
            href="/scam"
            className={`flex flex-col items-center justify-center p-1 rounded-lg text-xs font-medium ${pathname === "/scam" ? "text-[#0B4F43] font-bold" : "text-slate-600"
              }`}
          >
            <AlertTriangle className="w-5 h-5 mb-0.5" />
            <span className="text-[10px]">فراڈ چیک</span>
          </Link>
        </div>
      )}

      {/* ---------- Clean Footer ---------- */}
      <footer className="text-center text-xs text-slate-500 py-6 border-t border-slate-200 mt-auto">
        <p>رہبر (Rahbar) · The Last Mile: AI on Public Rails · Coder&apos;s Cup &apos;26</p>
      </footer>
    </div>
  );
}
