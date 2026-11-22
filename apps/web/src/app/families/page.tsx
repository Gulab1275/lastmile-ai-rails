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
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">مددگار موڈ · Field Worker Family Directory</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          ایک ٹچ سے خاندان تبدیل کریں اور ان کی طرف سے ریلیف گرانٹ کی درخواستیں جمع کرائیں۔ ہر خاندان کے پاس اپنی رضامندی کا مکمل اختیار ہے۔
        </p>
      </Card>

      {/* Active Family Card */}
      {selected && (
        <Card className="p-5 sm:p-6 border-[#0B4F43] bg-emerald-50/30 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-100 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-[#0B4F43] text-white flex items-center justify-center font-bold text-base shrink-0 shadow-sm">
                {selected.name.slice(0, 2)}
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#0B4F43]">
                  فعال خاندان · Active Citizen Context
                </span>
                <p className="text-lg font-bold text-slate-900 leading-snug">{selected.name}</p>
                <p className="text-xs text-slate-500 font-mono">CNIC: <span dir="ltr">{selected.cnic}</span></p>
              </div>
            </div>

            <div>
              {checkingConsent ? (
                <span className="text-xs text-slate-500">جانچ ہو رہی ہے...</span>
              ) : consent?.can_helper_act ? (
                <StatusBadge status="approved" labelUr="مجاز ہے" labelEn="Authorized" />
              ) : (
                <StatusBadge status="scam" labelUr="غیر مجاز" labelEn="Consent Missing" />
              )}
            </div>
          </div>

          {/* Consent Banner */}
          {consent && !consent.can_helper_act && (
            <div className="bg-amber-50 border border-amber-300 rounded-xl p-3.5 flex gap-3 text-xs">
              <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div className="space-y-0.5 text-amber-900">
                <p className="font-bold">اس خاندان نے ابھی مددگار کی اجازت نہیں دی</p>
                <p>فارم جمع کرانے کے لیے خاندان سے رضامندی پیج پر &ldquo;مددگار ورکر کے اختیارات&rdquo; فعال کروائیں۔</p>
              </div>
            </div>
          )}

          {consent?.can_helper_act && (
            <div className="bg-emerald-50 rounded-xl p-3 flex items-center gap-2 text-xs text-emerald-800 font-medium border border-emerald-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>مددگار کی قانونی اجازت فعال ہے — آپ درخواست اور کاغذات جمع کرا سکتے ہیں۔</span>
            </div>
          )}

          {error && (
            <div className="bg-rose-50 text-rose-800 rounded-xl p-3 font-medium text-xs border border-rose-200">
              {error}
            </div>
          )}

          {/* Action Buttons for Active Family */}
          <div className="grid grid-cols-3 gap-2.5 pt-1">
            <Link href="/apply">
              <Button variant="primary" className="w-full text-xs">
                نئی درخواست · Apply
              </Button>
            </Link>
            <Link href="/cases">
              <Button variant="secondary" className="w-full text-xs">
                کیسز · Cases
              </Button>
            </Link>
            <Link href="/consent">
              <Button variant="neutral" className="w-full text-xs">
                رضامندی · Consent
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute top-3.5 start-3.5 w-4 h-4 text-slate-400" />
        <input
          className="w-full min-h-[46px] border border-slate-300 rounded-xl ps-10 pe-10 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
          placeholder="نام یا شناختی کارڈ نمبر سے تلاش کریں / Search by name or CNIC"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {q && (
          <button
            onClick={() => setQ("")}
            className="absolute top-3.5 end-3.5 text-slate-400 hover:text-slate-700"
            type="button"
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
        <span>خاندانوں کی فہرست · Families Directory</span>
        <span>{shown.length} / {families.length}</span>
      </div>

      {/* Families Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {shown.map((f) => {
          const isSelected = selected?.id === f.id;

          return (
            <Card
              key={f.id}
              onClick={() => choose(f)}
              className={`p-4 text-start cursor-pointer transition border ${isSelected
                ? "border-[#0B4F43] bg-emerald-50/40 ring-1 ring-[#0B4F43]"
                : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-sm shrink-0 border border-slate-200">
                    {f.name.slice(0, 2)}
                  </div>
                  <div className="space-y-0.5">
                    <p className="font-bold text-sm text-slate-900 leading-snug">{f.name}</p>
                    <p className="text-xs text-slate-500 font-mono" dir="ltr">{f.cnic}</p>
                  </div>
                </div>

                {isSelected ? (
                  <span className="w-6 h-6 rounded-full bg-[#0B4F43] text-white flex items-center justify-center text-xs font-bold">
                    ✓
                  </span>
                ) : (
                  <span className="text-slate-400 group-hover:text-slate-600">
                    <UserRound className="w-4 h-4" />
                  </span>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </AppShell>
  );
}
