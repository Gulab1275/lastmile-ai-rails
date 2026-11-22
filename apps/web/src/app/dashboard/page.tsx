"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck, ScanSearch, FilePlus2, FolderOpen, Users, ClipboardList,
  SlidersHorizontal, ScrollText, BarChart3, Fingerprint, FileSearch, Map,
  Sparkles, ArrowLeft,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { NAV, getSession, type Session } from "@/lib/session";
import { useUI } from "@/lib/uiContext";

const ICONS: Record<string, React.ReactNode> = {
  "/apply": <FilePlus2 className="w-6 h-6" />,
  "/cases": <FolderOpen className="w-6 h-6" />,
  "/consent": <ShieldCheck className="w-6 h-6" />,
  "/scam": <ScanSearch className="w-6 h-6" />,
  "/families": <Users className="w-6 h-6" />,
  "/officer": <ClipboardList className="w-6 h-6" />,
  "/admin": <SlidersHorizontal className="w-6 h-6" />,
  "/auditor": <ScrollText className="w-6 h-6" />,
  "/eval": <BarChart3 className="w-6 h-6" />,
  "/identity": <Fingerprint className="w-6 h-6" />,
  "/documents": <FileSearch className="w-6 h-6" />,
  "/scam-map": <Map className="w-6 h-6" />,
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
      {/* Warm Sovereign Greeting Hero Card */}
      {session && (
        <div className="bg-[#0B4F43] text-white rounded-2xl p-6 shadow-sm border border-[#083e34] space-y-3">
          <div className="flex items-center justify-between">
            <span className="px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-emerald-200 inline-flex items-center gap-1.5 border border-white/15">
              <Sparkles className="w-3.5 h-3.5 text-[#F59E0B]" />
              <span>{t("رہبر ڈیجیٹل سروس", "Rahbar Digital Service")}</span>
            </span>
            <span className="text-xs font-mono uppercase bg-black/20 px-2.5 py-0.5 rounded text-emerald-100">
              {session.role}
            </span>
          </div>

          <div className="space-y-1.5 pt-1">
            <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white leading-tight">
              خوش آمدید، {session.username.replace("_", " ")}!
            </h2>
            <p className="text-sm text-emerald-100 leading-relaxed max-w-2xl">
              {t(
                "یہ آپ کا محفوظ ریلیف پورٹل ہے جہاں تمام فیصلے شفاف قواعد کے تحت ہوتے ہیں اور سسٹم کبھی کسی مستحق کو خود بخود مسترد نہیں کرتا۔",
                "This is your secure relief portal where decisions follow transparent rules and the system never auto-rejects eligible citizens."
              )}
            </p>
          </div>
        </div>
      )}

      {/* Quick Action Tiles */}
      <div className="space-y-3 pt-2">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          {t("اہم کارروائیاں · Quick Actions", "Quick Actions · اہم کارروائیاں")}
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          {session &&
            NAV[session.role]
              .filter((i) => i.href !== "/dashboard")
              .map((i) => {
                const info = DESC[i.href];
                return (
                  <Link key={i.href} href={i.href} className="group">
                    <Card className="p-4 sm:p-5 flex items-center gap-4 hover:border-[#0B4F43] hover:shadow-md transition active:scale-[0.99]">
                      <div className="w-12 h-12 rounded-xl bg-emerald-50 text-[#0B4F43] border border-emerald-100 flex items-center justify-center shrink-0 group-hover:bg-[#0B4F43] group-hover:text-white transition">
                        {ICONS[i.href]}
                      </div>
                      <div className="min-w-0 flex-1 space-y-0.5">
                        <div className="flex items-center justify-between">
                          <p className="text-sm sm:text-base font-bold text-slate-900 group-hover:text-[#0B4F43] transition truncate">
                            {lang === "ur" ? i.ur : i.en}
                          </p>
                          <ArrowLeft className="w-4 h-4 text-slate-400 group-hover:text-[#0B4F43] group-hover:-translate-x-1 rtl:rotate-0 rotate-180 transition shrink-0" />
                        </div>
                        {info && (
                          <p className="text-xs text-slate-500 leading-normal line-clamp-1">
                            {lang === "ur" ? info.ur : info.en}
                          </p>
                        )}
                      </div>
                    </Card>
                  </Link>
                );
              })}
        </div>
      </div>
    </AppShell>
  );
}
