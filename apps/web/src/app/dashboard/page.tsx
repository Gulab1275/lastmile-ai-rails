"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck, ScanSearch, FilePlus2, FolderOpen, Users, ClipboardList,
  SlidersHorizontal, ScrollText, BarChart3, Fingerprint, FileSearch, Map,
  Sparkles, ArrowLeft,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { NAV, getSession, type Session } from "@/lib/session";
import { useUI } from "@/lib/uiContext";

const ICONS: Record<string, React.ReactNode> = {
  "/apply": <FilePlus2 className="w-8 h-8" />,
  "/cases": <FolderOpen className="w-8 h-8" />,
  "/consent": <ShieldCheck className="w-8 h-8" />,
  "/scam": <ScanSearch className="w-8 h-8" />,
  "/families": <Users className="w-8 h-8" />,
  "/officer": <ClipboardList className="w-8 h-8" />,
  "/admin": <SlidersHorizontal className="w-8 h-8" />,
  "/auditor": <ScrollText className="w-8 h-8" />,
  "/eval": <BarChart3 className="w-8 h-8" />,
  "/identity": <Fingerprint className="w-8 h-8" />,
  "/documents": <FileSearch className="w-8 h-8" />,
  "/scam-map": <Map className="w-8 h-8" />,
};

const DESC: Record<string, { ur: string; en: string }> = {
  "/apply": { ur: "نئی ریلیف گرانٹ کی درخواست کا راستہ", en: "Start a relief grant application" },
  "/cases": { ur: "اپنی جمع شدہ درخواستوں کی لائیو پیشرفت دیکھیں", en: "Track your cases and status" },
  "/consent": { ur: "معلوم کریں آپ کا ڈیٹا کس ادارے کے پاس ہے", en: "Manage who has access to your data" },
  "/scam": { ur: "مشکوک SMS یا واٹس ایپ میسج کی AI سے جانچ", en: "Analyze fraudulent relief messages" },
  "/families": { ur: "مختلف خاندانوں کے درمیان باآسانی سوئچ کریں", en: "Switch between family files" },
  "/officer": { ur: "کم اعتماد والے کیسز کا انسانی جائزہ اور تصدیق", en: "Review cases flagged for human verification" },
  "/admin": { ur: "پالیسی قواعد کی تبدیلی اور پبلک ریلز API چابیاں", en: "Simulate policy rules & manage API keys" },
  "/auditor": { ur: "کرپٹوگرافک SHA-256 آڈٹ لاگ اور ہیش چین", en: "Inspect immutable audit hash ledger" },
  "/eval": { ur: "اے آئی ماڈلز کے تصدیقی نتائج اور ضمانتیں", en: "Model accuracy & cost sweep curves" },
  "/identity": { ur: "نادرا ڈیٹا بیس سے شناختی کارڈ کا فزی میچ", en: "NADRA biometric similarity check" },
  "/documents": { ur: "بجلی کے بل اور شناختی کارڈ کی دھندلاہٹ جانچ", en: "Document OCR and blur gate testing" },
  "/scam-map": { ur: "پاکستان میں ریلیف فراڈ کے علاقائی کلسٹرز", en: "Geographic scam threat cluster map" },
};

export default function Dashboard() {
  const [session, setSession] = useState<Session | null>(null);
  const { lang, t } = useUI();

  useEffect(() => {
    setSession(getSession());
  }, []);

  return (
    <AppShell title={t("خوش آمدید · Welcome", "Welcome · خوش آمدید")}>
      {/* Warm Nastaliq Greeting Hero Card */}
      {session && (
        <div className="relative overflow-hidden bg-gradient-to-br from-[#0B4F43] via-[#0F6B5A] to-[#0B4F43] text-white rounded-3xl p-6 shadow-lift border border-white/10 space-y-3">
          <div className="pattern-dots absolute inset-0 opacity-20 pointer-events-none" aria-hidden="true" />
          <div className="relative z-10 flex items-center justify-between">
            <span className="px-3 py-1 bg-white/20 backdrop-blur rounded-full text-xs font-bold text-[#DDEFE9] inline-flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#E8A33D]" />
              <span>{t("رہبر ڈیجیٹل سروس", "Rahbar Digital Service")}</span>
            </span>
            <span className="text-[11px] font-mono uppercase bg-black/25 px-2.5 py-0.5 rounded-full text-[#DDEFE9]">
              {session.role}
            </span>
          </div>

          <div className="relative z-10 space-y-1">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading text-white leading-tight">
              خوش آمدید، {session.username.replace("_", " ")}!
            </h2>
            <p className="text-sm sm:text-base text-[#DDEFE9] font-body leading-relaxed">
              {t(
                "یہ آپ کا محفوظ ریلیف پورٹل ہے جہاں تمام فیصلے شفاف قواعد کے تحت ہوتے ہیں اور سسٹم کبھی کسی مستحق کو خود بخود مسترد نہیں کرتا۔",
                "This is your secure relief portal where decisions follow transparent rules and the system never auto-rejects eligible citizens."
              )}
            </p>
          </div>
        </div>
      )}

      {/* Role-Specific Quick Actions Cards Grid (No fake numbers) */}
      <div className="space-y-2 pt-1">
        <p className="text-xs font-bold text-[#5B6F6A] uppercase tracking-wider">
          {t("اہم اقدامات · Quick Actions", "Quick Actions · اہم اقدامات")}
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          {session &&
            NAV[session.role]
              .filter((i) => i.href !== "/dashboard")
              .map((i) => {
                const info = DESC[i.href];
                return (
                  <Link key={i.href} href={i.href} className="group">
                    <div className="bg-white rounded-3xl shadow-sm border border-[#E2DDD3] p-5 flex items-center gap-4 min-h-[96px] group-hover:border-[#0B4F43] group-hover:shadow-md transition active:scale-[0.99]">
                      <div className="w-14 h-14 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center shrink-0 group-hover:bg-[#0B4F43] group-hover:text-[#E8A33D] transition">
                        {ICONS[i.href]}
                      </div>
                      <div className="space-y-1 min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-base font-bold text-[#17302B] group-hover:text-[#0B4F43] transition font-heading truncate">
                            {lang === "ur" ? i.ur : i.en}
                          </p>
                          <ArrowLeft className="w-4 h-4 text-[#5B6F6A] group-hover:text-[#0B4F43] group-hover:-translate-x-1 rtl:rotate-0 rotate-180 transition" />
                        </div>
                        {info && (
                          <p className="text-xs text-[#5B6F6A] leading-snug line-clamp-1 font-body">
                            {lang === "ur" ? info.ur : info.en}
                          </p>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })}
        </div>
      </div>
    </AppShell>
  );
}
