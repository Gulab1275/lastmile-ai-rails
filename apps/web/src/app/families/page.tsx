"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Search, UserRound, CheckCircle2, ShieldAlert,
  ArrowRight, X,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type ConsentStatus, type Family } from "@/lib/api";
import { getActiveCitizenId, setActiveCitizen, speak } from "@/lib/session";

const AVATAR_ACCENTS = [
  { border: "border-[#0B4F43]", bg: "bg-[#DDEFE9]", text: "text-[#0B4F43]" },
  { border: "border-[#0284C7]", bg: "bg-[#E0F2FE]", text: "text-[#0369A1]" },
  { border: "border-[#E8A33D]", bg: "bg-[#FEF3C7]", text: "text-[#92400E]" },
  { border: "border-[#4C5FD5]", bg: "bg-[#EEF2FF]", text: "text-[#3730A3]" },
  { border: "border-[#D946EF]", bg: "bg-[#FDF4FF]", text: "text-[#86198F]" },
];

export default function FamiliesPage() {
  const [families, setFamilies] = useState<Family[]>([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Family | null>(null);
  const [consent, setConsent] = useState<ConsentStatus | null>(null);
  const [checkingConsent, setCheckingConsent] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getFamilies().then((f) => {
      setFamilies(f);
      const active = getActiveCitizenId();
      const found = f.find((x) => x.id === active);
      if (found) {
        choose(found, false);
      }
    }).catch((e: ApiError) => setError(e.message_ur ?? e.message_en ?? "Could not load families"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function choose(f: Family, announce = true) {
    setActiveCitizen(f.id, f.name);
    setSelected(f);
    setConsent(null);
    setError("");
    setCheckingConsent(true);
    if (announce) {
      speak(`${f.name} منتخب ہو گیا`, "ur-PK");
    }
    try {
      const res = await api.getConsentStatus(f.id);
      setConsent(res);
    } catch (e) {
      setError((e as ApiError).message_ur ?? (e as ApiError).message_en ?? "Consent check failed");
    } finally {
      setCheckingConsent(false);
    }
  }

  const shown = families.filter((f) =>
    (f.name + f.cnic).toLowerCase().includes(q.toLowerCase())
  );

  return (
    <AppShell title="میرے زیرِ کفالت خاندان · Helper Family Hub">
      <Card className="p-5 space-y-2">
        <h2 className="text-xl font-bold text-[#0B4F43]">مددگار موڈ · Field Worker Family Switcher</h2>
        <p className="text-sm text-[#5B6F6A]">
          ایک ٹچ سے خاندان تبدیل کریں اور ان کی طرف سے ریلیف گرانٹ کی درخواستیں جمع کرائیں۔ ہر خاندان کے پاس اپنی رضامندی کا مکمل اختیار ہے۔
        </p>
      </Card>

      {/* Active Family Card */}
      {selected && (
        <div className="bg-white rounded-3xl p-5 border-2 border-[#0B4F43] shadow-lift space-y-4 animate-fade-up">
          <div className="flex items-center justify-between border-b border-[#E2DDD3] pb-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center font-bold text-lg shadow-sm border border-[#1F8A5B]">
                {selected.name.slice(0, 2)}
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#0B4F43]">
                  منتخب خاندان · Active Citizen
                </span>
                <p className="text-xl font-bold text-[#17302B] leading-tight">{selected.name}</p>
                <p className="text-xs text-[#5B6F6A] font-mono">CNIC: {selected.cnic}</p>
              </div>
            </div>

            <div>
              {checkingConsent ? (
                <span className="text-xs text-[#5B6F6A] animate-pulse">جانچ ہو رہی ہے...</span>
              ) : consent?.can_helper_act ? (
                <StatusBadge status="approved" labelUr="مجاز ہے" labelEn="Authorized" />
              ) : (
                <StatusBadge status="scam" labelUr="غیر مجاز" labelEn="Consent Missing" />
              )}
            </div>
          </div>

          {/* Consent Status Notification */}
          {consent && !consent.can_helper_act && (
            <div className="bg-[#FEF3C7] border-2 border-[#C77700] rounded-2xl p-4 flex gap-3 text-start">
              <ShieldAlert className="w-6 h-6 text-[#C77700] shrink-0 mt-0.5" />
              <div className="text-xs space-y-1 text-[#78350F]">
                <p className="font-bold text-sm text-[#92400E]">
                  اس خاندان نے ابھی مددگار کی اجازت نہیں دی
                </p>
                <p>
                  فارم جمع کرانے کے لیے خاندان سے رضامندی پیج پر &ldquo;مددگار ورکر کے اختیارات&rdquo; آن کروائیں۔
                </p>
              </div>
            </div>
          )}

          {consent?.can_helper_act && (
            <div className="bg-[#DDEFE9] rounded-2xl p-3 flex items-center gap-2 text-xs text-[#065F46] font-bold">
              <CheckCircle2 className="w-5 h-5 text-[#1F8A5B]" />
              <span>مددگار کی قانونی اجازت فعال ہے — آپ درخواست اور کاغذات جمع کرا سکتے ہیں۔</span>
            </div>
          )}

          {error && (
            <div className="bg-[#FEE2E2] text-[#991B1B] rounded-2xl p-3 font-bold text-xs">
              {error}
            </div>
          )}

          {/* Quick Actions for Selected Citizen */}
          <div className="grid grid-cols-3 gap-2 text-center pt-1">
            <Link href="/apply">
              <Button variant="primary" className="w-full text-xs sm:text-sm">
                نئی درخواست · Apply
              </Button>
            </Link>
            <Link href="/cases">
              <Button variant="secondary" className="w-full text-xs sm:text-sm">
                کیس دیکھیں · Cases
              </Button>
            </Link>
            <Link href="/consent">
              <Button variant="neutral" className="w-full text-xs sm:text-sm">
                رضامندی · Consent
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute top-4 start-4 w-5 h-5 text-[#5B6F6A]" />
        <input
          className="w-full min-h-[54px] border-2 border-[#E2DDD3] rounded-2xl ps-12 pe-10 text-base bg-white text-[#17302B] font-medium focus:border-[#0B4F43] focus:outline-none transition shadow-sm"
          placeholder="نام، شناختی کارڈ یا فون سے تلاش کریں / Search family"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {q && (
          <button
            onClick={() => setQ("")}
            className="absolute top-4 end-4 text-[#5B6F6A] hover:text-[#17302B]"
            type="button"
            aria-label="Clear search"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-[#5B6F6A] px-1 font-bold">
        <span>خاندانوں کی فہرست · Families Directory</span>
        <span>{shown.length} / {families.length}</span>
      </div>

      {/* Families Grid (Picture / Medallion Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {shown.map((f, idx) => {
          const isSelected = selected?.id === f.id;
          const accent = AVATAR_ACCENTS[idx % AVATAR_ACCENTS.length];

          return (
            <Card
              key={f.id}
              onClick={() => choose(f)}
              className={`p-4 text-start cursor-pointer transition-all duration-200 border-2 ${
                isSelected
                  ? "border-[#0B4F43] bg-[#DDEFE9]/30 ring-2 ring-[#0B4F43]/30 shadow-md scale-[1.01]"
                  : "border-[#E2DDD3] hover:border-[#0B4F43]/50 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-12 h-12 rounded-2xl ${accent.bg} ${accent.text} border-2 ${accent.border} flex items-center justify-center font-bold text-base shadow-sm shrink-0`}
                  >
                    {f.name.slice(0, 2)}
                  </div>
                  <div>
                    <p className="font-bold text-[#17302B] text-base leading-snug">{f.name}</p>
                    <p className="text-xs text-[#5B6F6A] font-mono mt-0.5">{f.cnic}</p>
                  </div>
                </div>

                {isSelected ? (
                  <span className="w-7 h-7 rounded-full bg-[#0B4F43] text-white flex items-center justify-center text-xs font-bold shadow-sm">
                    ✓
                  </span>
                ) : (
                  <span className="w-7 h-7 rounded-full bg-[#E2DDD3]/60 text-[#5B6F6A] flex items-center justify-center text-xs">
                    <UserRound className="w-3.5 h-3.5" />
                  </span>
                )}
              </div>

              <div className="mt-3 pt-2.5 border-t border-[#E2DDD3] flex items-center justify-between text-xs">
                <span className="text-[#5B6F6A]">کلک کر کے کام شروع کریں</span>
                <span className="text-[#0B4F43] font-bold flex items-center gap-1">
                  منتخب کریں <ArrowRight className="w-3 h-3 rtl:rotate-180" />
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      {shown.length === 0 && (
        <Card className="p-8 text-center space-y-3">
          <p className="text-base font-bold text-[#17302B]">کوئی خاندان نہیں ملا · No families match search</p>
          <p className="text-xs text-[#5B6F6A]">تلاش کے الفاظ تبدیل کر کے دوبارہ کوشش کریں۔</p>
        </Card>
      )}
    </AppShell>
  );
}
