"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Wifi, WifiOff } from "lucide-react";
import { NAV, clearSession, getSession, type Session } from "@/lib/session";

const ROLE_LABEL: Record<string, string> = {
  citizen: "شہری / Citizen",
  helper: "مددگار / Helper",
  officer: "افسر / Officer",
  admin: "ایڈمن / Admin",
  auditor: "آڈیٹر / Auditor",
};

export default function AppShell({
  children,
  title,
}: {
  children: React.ReactNode;
  title?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [session, setSession] = useState<Session | null>(null);
  const [online, setOnline] = useState(true);

  useEffect(() => {
    const s = getSession();
    if (!s) {
      router.replace("/");
      return;
    }
    setSession(s);
    setOnline(navigator.onLine);
    const up = () => setOnline(true);
    const down = () => setOnline(false);
    window.addEventListener("online", up);
    window.addEventListener("offline", down);
    return () => {
      window.removeEventListener("online", up);
      window.removeEventListener("offline", down);
    };
  }, [router]);

  if (!session) return null;

  return (
    <div className="min-h-screen bg-emerald-50">
      <header className="bg-emerald-700 text-white">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xl font-bold">رہبر Rahbar</p>
            <p className="text-sm text-emerald-100">
              {ROLE_LABEL[session.role]} · {session.username}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {online ? (
              <Wifi className="w-6 h-6" aria-label="online" />
            ) : (
              <WifiOff className="w-6 h-6 text-amber-300" aria-label="offline" />
            )}
            <button
              onClick={() => {
                clearSession();
                router.replace("/");
              }}
              className="h-12 w-12 flex items-center justify-center rounded-2xl bg-emerald-800"
              aria-label="Logout"
            >
              <LogOut className="w-6 h-6" />
            </button>
          </div>
        </div>
        <nav className="max-w-3xl mx-auto px-4 pb-3 flex gap-2 overflow-x-auto">
          {NAV[session.role].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`h-12 px-5 flex items-center rounded-2xl whitespace-nowrap font-bold ${
                pathname === item.href ? "bg-white text-emerald-800" : "bg-emerald-600 text-white"
              }`}
            >
              {item.ur} · {item.en}
            </Link>
          ))}
        </nav>
      </header>

      {!online && (
        <div className="bg-amber-100 text-amber-900 text-center py-2 font-bold">
          انٹرنیٹ بند ہے · You are offline — changes will sync later
        </div>
      )}

      <main className="max-w-3xl mx-auto p-4 space-y-4">
        {title && <h1 className="text-2xl font-bold text-emerald-800">{title}</h1>}
        {children}
      </main>
    </div>
  );
}