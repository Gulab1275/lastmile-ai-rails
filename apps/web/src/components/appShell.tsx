"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, UserRound } from "lucide-react";
import { NAV, clearSession, getActiveCitizenName, getSession, type Session } from "@/lib/session";
import { NAV_ICONS } from "@/lib/navIcons";
import { flushQueue, queuedCount } from "@/lib/offlineQueue";
import Logo from "@/components/logo";

const ROLE_LABEL: Record<string, string> = {
  citizen: "شہری · Citizen",
  helper: "مددگار · Helper",
  officer: "افسر · Officer",
  admin: "ایڈمن · Admin",
  auditor: "آڈیٹر · Auditor",
};

export default function AppShell({ children, title }: { children: React.ReactNode; title?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const [session, setSession] = useState<Session | null>(null);
  const [online, setOnline] = useState(true);
  const [pending, setPending] = useState(0);
  const [syncMsg, setSyncMsg] = useState("");
  const [acting, setActing] = useState("");

  const sync = useCallback(async (userId: string) => {
    try {
      const n = await flushQueue(userId);
      if (n > 0) setSyncMsg(`${n} آف لائن فارم بھیج دیے گئے · ${n} offline form(s) synced`);
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
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, [router, sync]);

  if (!session) return null;

  const initials = session.username.split("_").map((p) => p[0]?.toUpperCase()).join("").slice(0, 2);

  return (
    <div className="min-h-screen">
      {/* ---------- Header ---------- */}
      <header className="relative overflow-hidden bg-gradient-to-br from-emerald-900 via-emerald-700 to-teal-600 text-white rounded-b-[2rem] shadow-lift">
        <div className="pattern-dots absolute inset-0 opacity-60" aria-hidden="true" />
        <div className="relative max-w-3xl mx-auto px-4 pt-4 pb-5 flex items-center gap-3">
          <Logo size={46} />
          <div className="flex-1 min-w-0">
            <p className="text-2xl font-bold leading-tight">رہبر · Rahbar</p>
            <p className="text-xs text-emerald-100 truncate">Relief that finds its way to those who need it</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 bg-white/15 rounded-full ps-2 pe-3 py-1 text-xs font-bold">
              <span className={`w-2.5 h-2.5 rounded-full ${online ? "bg-emerald-300 animate-pulse-dot" : "bg-amber-400"}`} />
              {online ? "Online" : "Offline"}
            </span>
            <button
              onClick={() => { clearSession(); router.replace("/"); }}
              className="h-11 w-11 flex items-center justify-center rounded-2xl bg-white/15 hover:bg-white/25"
              aria-label="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
        <div className="relative max-w-3xl mx-auto px-4 pb-4 flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-amber-300 to-amber-500 text-amber-950 font-bold flex items-center justify-center shadow">
            {initials}
          </div>
          <div className="leading-tight">
            <p className="font-bold">{session.username}</p>
            <p className="text-xs text-emerald-100">{ROLE_LABEL[session.role]}</p>
          </div>
        </div>
      </header>

      {/* ---------- Sticky menu ---------- */}
      <nav className="sticky top-0 z-30 glass border-b border-emerald-100 mt-3">
        <div className="max-w-3xl mx-auto px-3 py-2 flex gap-2 overflow-x-auto scrollbar-none">
          {NAV[session.role].map((item) => {
            const Icon = NAV_ICONS[item.href];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`h-11 px-4 flex items-center gap-2 rounded-full whitespace-nowrap font-bold text-sm transition ${
                  active
                    ? "bg-gradient-to-br from-emerald-600 to-teal-600 text-white shadow-lift"
                    : "bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
                }`}
              >
                {Icon && <Icon className="w-4 h-4" />}
                {item.ur} · {item.en}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* ---------- Status strips ---------- */}
      {!online && (
        <div className="bg-amber-100 text-amber-900 text-center py-2 font-bold">
          انٹرنیٹ بند ہے · You are offline — forms are saved on this phone
        </div>
      )}
      {pending > 0 && (
        <div className="bg-sky-100 text-sky-900 text-center py-2 font-bold">
          {pending} فارم بھیجنے کے منتظر · {pending} form(s) waiting to sync
        </div>
      )}
      {syncMsg && <div className="bg-emerald-200 text-emerald-900 text-center py-2 font-bold">{syncMsg}</div>}
      {session.role === "helper" && acting && (
        <div className="bg-amber-50 border-b border-amber-200 text-center py-2 font-bold text-amber-900 flex items-center justify-center gap-2">
          <UserRound className="w-5 h-5" /> آپ کام کر رہے ہیں · Acting for: {acting}
        </div>
      )}

      {/* ---------- Page content ---------- */}
      <main className="max-w-3xl mx-auto p-4 pb-16 space-y-4 stagger">
        {title && <h1 className="text-2xl font-bold text-emerald-900">{title}</h1>}
        {children}
      </main>

      <footer className="text-center text-xs text-emerald-800/60 pb-6">
        Rahbar · The Last Mile AI on Public Rails · Prototype
      </footer>
    </div>
  );
}