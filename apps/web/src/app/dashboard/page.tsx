"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ShieldCheck, ScanSearch, Clock } from "lucide-react";
import AppShell from "@/components/appShell";
import { getSession } from "@/lib/session";
import type { Role } from "@/lib/api";

type Card = { href?: string; en: string; ur: string; icon: React.ReactNode };

const ICON = "w-10 h-10";
const CARDS: Record<Role, Card[]> = {
  citizen: [
    { href: "/consent", en: "Who has my data?", ur: "میرا ڈیٹا کس کے پاس ہے؟", icon: <ShieldCheck className={ICON} /> },
    { href: "/scam", en: "Check a suspicious SMS", ur: "مشکوک میسج چیک کریں", icon: <ScanSearch className={ICON} /> },
  ],
  helper: [
    { href: "/consent", en: "Family consent", ur: "خاندان کی رضامندی", icon: <ShieldCheck className={ICON} /> },
    { href: "/scam", en: "Scam checker", ur: "فراڈ چیکر", icon: <ScanSearch className={ICON} /> },
  ],
  officer: [{ en: "Review queue (next batch)", ur: "ریویو قطار", icon: <Clock className={ICON} /> }],
  admin: [{ en: "Rule editor (next batch)", ur: "رول ایڈیٹر", icon: <Clock className={ICON} /> }],
  auditor: [{ en: "Audit log (next batch)", ur: "آڈٹ لاگ", icon: <Clock className={ICON} /> }],
};

export default function Dashboard() {
  const [role, setRole] = useState<Role | null>(null);
  useEffect(() => setRole(getSession()?.role ?? null), []);

  return (
    <AppShell title="خوش آمدید · Welcome">
      <div className="grid gap-4">
        {role &&
          CARDS[role].map((c) => {
            const body = (
              <div className="bg-white rounded-3xl shadow p-6 flex items-center gap-4 min-h-24">
                <div className="text-emerald-600">{c.icon}</div>
                <div>
                  <p className="text-xl font-bold">{c.ur}</p>
                  <p className="text-gray-500">{c.en}</p>
                </div>
              </div>
            );
            return c.href ? (
              <Link key={c.en} href={c.href}>{body}</Link>
            ) : (
              <div key={c.en} className="opacity-60">{body}</div>
            );
          })}
      </div>
    </AppShell>
  );
}