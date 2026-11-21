"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck, ScanSearch, FilePlus2, FolderOpen, Users, ClipboardList, SlidersHorizontal, ScrollText, BarChart3,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { NAV, getSession } from "@/lib/session";
import type { Role } from "@/lib/api";

const ICON = "w-10 h-10";
const ICONS: Record<string, React.ReactNode> = {
  "/apply": <FilePlus2 className={ICON} />,
  "/cases": <FolderOpen className={ICON} />,
  "/consent": <ShieldCheck className={ICON} />,
  "/scam": <ScanSearch className={ICON} />,
  "/families": <Users className={ICON} />,
  "/officer": <ClipboardList className={ICON} />,
  "/admin": <SlidersHorizontal className={ICON} />,
  "/auditor": <ScrollText className={ICON} />,
  "/eval": <BarChart3 className={ICON} />,
};
const DESC: Record<string, string> = {
  "/apply": "نئی درخواست دیں · Start a new application",
  "/cases": "درخواست کی حالت دیکھیں · Track your case",
  "/consent": "میرا ڈیٹا کس کے پاس ہے؟ · Who has my data?",
  "/scam": "مشکوک میسج چیک کریں · Check a suspicious SMS",
  "/families": "خاندان بدلیں · Switch between families",
  "/officer": "جانچ طلب کیسز · Cases that need a human",
  "/admin": "قواعد بدلیں اور آزمائیں · Edit and simulate rules",
  "/auditor": "ہر فیصلے کا ریکارڈ · Tamper-proof record",
  "/eval": "اے آئی کی کارکردگی · How well the AI performs",
};

export default function Dashboard() {
  const [role, setRole] = useState<Role | null>(null);
  useEffect(() => setRole(getSession()?.role ?? null), []);

  return (
    <AppShell title="خوش آمدید · Welcome">
      <div className="grid gap-4">
        {role &&
          NAV[role]
            .filter((i) => i.href !== "/dashboard")
            .map((i) => (
              <Link key={i.href} href={i.href}>
                <div className="bg-white rounded-3xl shadow p-6 flex items-center gap-4 min-h-24">
                  <div className="text-emerald-600">{ICONS[i.href]}</div>
                  <div>
                    <p className="text-xl font-bold">{i.ur}</p>
                    <p className="text-gray-500">{DESC[i.href] ?? i.en}</p>
                  </div>
                </div>
              </Link>
            ))}
      </div>
    </AppShell>
  );
}