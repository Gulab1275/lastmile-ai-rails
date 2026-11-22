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
    <div className="min-h-screen bg-[#F7F4EE] text-[#17302B]">
      {/* ---------- Header ---------- */}
      <header className="relative overflow-hidden bg-gradient-to-br from-[#0B4F43] via-[#0F6B5A] to-[#0B4F43] text-white rounded-b-[2rem] shadow-lift">
        <div className="pattern-dots absolute inset-0 opacity-40" aria-hidden="true" />
        <div className="relative max-w-3xl mx-auto px-4 pt-4 pb-4 flex items-center gap-3">
          <Logo size={44} />
          <div className="flex-1 min-w-0">
            <p className="text-2xl font-bold leading-tight">رہبر · Rahbar</p>
            <p className="text-xs text-[#DDEFE9] truncate">The Last Mile AI on Public Rails</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 bg-white/15 rounded-full ps-2 pe-3 py-1 text-xs font-bold">
              <span className={`w-2.5 h-2.5 rounded-full ${online ? "bg-[#34D399] animate-pulse-dot" : "bg-[#E8A33D]"}`} />
              {online ? "Online" : "Offline"}
            </span>
            <button
              onClick={() => { clearSession(); router.replace("/"); }}
              className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-2xl bg-white/15 hover:bg-white/25"
              aria-label="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
        <div className="relative max-w-3xl mx-auto px-4 pb-4 flex items-center gap-3 border-t border-white/10 pt-3">
          <div className="h-10 w-10 rounded-full bg-[#E8A33D] text-[#17302B] font-bold flex items-center justify-center shadow">
            {initials}
          </div>
          <div className="leading-tight">
            <p className="font-bold">{session.username}</p>
            <p className="text-xs text-[#DDEFE9]">{ROLE_LABEL[session.role]}</p>
          </div>
        </div>
      </header>

      {/* ---------- Sticky menu ---------- */}
      <nav className="sticky top-0 z-30 bg-[#F7F4EE]/95 backdrop-blur border-b border-[#E2DDD3] mt-2 shadow-sm">
        <div className="max-w-3xl mx-auto px-3 py-2 flex gap-2 overflow-x-auto scrollbar-none">
          {NAV[session.role].map((item) => {
            const Icon = NAV_ICONS[item.href];
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`min-h-[44px] px-4 flex items-center gap-2 rounded-2xl whitespace-nowrap font-bold text-sm transition ${
                  active
                    ? "bg-[#0B4F43] text-white shadow-lift"
                    : "bg-white text-[#17302B] hover:bg-[#DDEFE9] border border-[#E2DDD3]"
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
        <div className="bg-[#FEF3C7] text-[#92400E] border-b border-[#FCD34D] text-center py-2.5 font-bold text-sm">
          انٹرنیٹ بند ہے · Offline mode active — forms saved safely on device
        </div>
      )}
      {pending > 0 && (
        <div className="bg-[#E0F2FE] text-[#075985] text-center py-2.5 font-bold text-sm">
          {pending} فارم بھیجنے کے منتظر · {pending} form(s) waiting to sync
        </div>
      )}
      {syncMsg && <div className="bg-[#D1FAE5] text-[#065F46] text-center py-2.5 font-bold text-sm">{syncMsg}</div>}
      {session.role === "helper" && acting && (
        <div className="bg-[#FFFBEB] border-b border-[#FDE68A] text-center py-2.5 font-bold text-[#92400E] flex items-center justify-center gap-2">
          <UserRound className="w-5 h-5 text-[#E8A33D]" /> آپ کام کر رہے ہیں · Acting for: <span className="underline">{acting}</span>
        </div>
      )}

      {/* ---------- Page content ---------- */}
      <main className={`max-w-3xl mx-auto p-4 pb-16 space-y-4 stagger ${session.role === "citizen" || session.role === "helper" ? "text-[18px]" : ""}`}>
        {title && <h1 className="text-2xl font-bold text-[#0B4F43]">{title}</h1>}
        {children}
      </main>

      <footer className="text-center text-xs text-[#5B6F6A] pb-6">
        Rahbar · The Last Mile AI on Public Rails · Prototype
      </footer>
    </div>
  );
}
