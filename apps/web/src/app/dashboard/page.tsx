"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck, ScanSearch, FilePlus2, FolderOpen, Users, ClipboardList,
  SlidersHorizontal, ScrollText, BarChart3, Fingerprint, FileSearch, Map, Sparkles,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { NAV, getSession, type Session } from "@/lib/session";

const ICON = "w-8 h-8";
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
  "/identity": <Fingerprint className={ICON} />,
  "/documents": <FileSearch className={ICON} />,
  "/scam-map": <Map className={ICON} />,
};

const DESC: Record<string, { ur: string; en: string }> = {
  "/apply": { ur: "نئی ریلیف گرانٹ کی درخواست جمع کرائیں", en: "Apply for relief grant" },
  "/cases": { ur: "اپنی جمع شدہ درخواستوں کی پیشرفت دیکھیں", en: "Track submitted cases" },
  "/consent": { ur: "معلوم کریں آپ کا ڈیٹا کس کے پاس ہے", en: "Manage data consents" },
  "/scam": { ur: "مشکوک SMS یا واٹس ایپ میسج کی جانچ کریں", en: "Scan suspicious SMS" },
  "/families": { ur: "مختلف خاندانوں کے درمیان سوئچ کریں", en: "Switch family context" },
  "/officer": { ur: "کم اعتماد والے کیسز کی انسانی تصدیق", en: "Human review queue" },
  "/admin": { ur: "پالیسی قواعد اور پبلک ریلز API چابیاں", en: "Policy rules & API keys" },
  "/auditor": { ur: "کرپٹوگرافک آڈٹ لاگ اور ہیش چین کا معائنہ", en: "Cryptographic audit trail" },
  "/eval": { ur: "اے آئی ماڈلز کی کارکردگی اور ضمانتیں", en: "Model evaluation & curves" },
  "/identity": { ur: "نادرا ڈیٹا بیس سے شناختی کارڈ کی تصدیق", en: "NADRA identity verification" },
  "/documents": { ur: "بجلی کے بل اور کاغذات کا OCR اور معائنہ", en: "Document OCR & blur gate" },
  "/scam-map": { ur: "پاکستان میں فراڈ ہاٹ اسپاٹس کا نقشہ", en: "Geographic scam threat map" },
};

export default function Dashboard() {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  return (
    <AppShell title="ڈیش بورڈ · Quick Navigation">
      {/* Personalized Welcome Card */}
      {session && (
        <div className="bg-gradient-to-br from-[#0B4F43] to-[#0F6B5A] text-white rounded-3xl p-6 shadow-lift space-y-2 border border-white/10">
          <div className="flex items-center justify-between">
            <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-bold text-[#DDEFE9] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#E8A33D]" /> خوش آمدید · Welcome
            </span>
            <span className="text-xs uppercase font-mono text-[#DDEFE9] tracking-wider">Role: {session.role}</span>
          </div>
          <h2 className="text-2xl font-bold">{session.username}</h2>
          <p className="text-xs text-[#DDEFE9]">
            ڈیجیٹل پبلک انفراسٹرکچر (DPI) پر مبنی ریلیف سسٹم۔ نیچے دیئے گئے آپشنز میں سے انتخاب کریں۔
          </p>
        </div>
      )}

      {/* Role Navigation Grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {session &&
          NAV[session.role]
            .filter((i) => i.href !== "/dashboard")
            .map((i) => {
              const info = DESC[i.href];
              return (
                <Link key={i.href} href={i.href} className="group">
                  <div className="bg-white rounded-3xl shadow-sm border border-[#E2DDD3] p-5 flex items-center gap-4 min-h-[90px] group-hover:border-[#0B4F43] group-hover:shadow-md transition">
                    <div className="w-12 h-12 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center shrink-0 group-hover:bg-[#0B4F43] group-hover:text-[#E8A33D] transition">
                      {ICONS[i.href]}
                    </div>
                    <div className="space-y-0.5 min-w-0 flex-1">
                      <p className="text-base font-bold text-[#17302B] group-hover:text-[#0B4F43] transition truncate">
                        {i.ur} · {i.en}
                      </p>
                      {info && (
                        <p className="text-xs text-[#5B6F6A] leading-snug line-clamp-1">
                          {info.ur}
                        </p>
                      )}
                    </div>
                  </div>
                </Link>
              );
            })}
      </div>
    </AppShell>
  );
}
