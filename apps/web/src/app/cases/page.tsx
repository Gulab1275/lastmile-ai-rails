"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Volume2, ChevronDown, ChevronUp, FileText, CheckCircle2,
  AlertTriangle, HelpCircle, ArrowRight, ShieldCheck,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge, type StatusBadgeProps } from "@/components/ui/StatusBadge";
import api, { type ApiError, type CaseItem, type CaseStatus } from "@/lib/api";
import { getSession, speak } from "@/lib/session";

const STATUS_MAP: Record<CaseStatus, { badge: StatusBadgeProps["status"]; ur: string; en: string; step: number }> = {
  draft: { badge: "draft", ur: "مسودہ", en: "Draft", step: 1 },
  submitted: { badge: "draft", ur: "جمع ہو گئی", en: "Submitted", step: 1 },
  processing: { badge: "draft", ur: "کارروائی جاری", en: "Processing", step: 2 },
  in_review: { badge: "in_review", ur: "افسر دیکھ رہا ہے", en: "With Officer", step: 2 },
  need_proof: { badge: "need_proof", ur: "مزید ثبوت درکار", en: "Proof Needed", step: 2 },
  need_more_info: { badge: "need_proof", ur: "معلومات درکار", en: "Info Needed", step: 2 },
  approved: { badge: "approved", ur: "منظور شدہ", en: "Approved", step: 3 },
  disbursed: { badge: "disbursed", ur: "رقم ادا ہو گئی", en: "Disbursed", step: 4 },
  rejected: { badge: "need_proof", ur: "مسترد", en: "Declined", step: 3 },
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[] | null>(null);
  const [open, setOpen] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const active = localStorage.getItem("active_citizen");
    const isHelper = getSession()?.role === "helper";
    api.listCases()
      .then((all) => setCases(isHelper && active ? all.filter((c) => c.citizen_id === active) : all))
      .catch((e: ApiError) => setError(e.message_ur ?? e.message_en ?? "Error loading cases"));
  }, []);

  return (
    <AppShell title="میرے ریلیف کیسز · Case Tracking">
      {error && (
        <div className="bg-rose-50 text-rose-800 border border-rose-200 rounded-xl p-4 font-medium text-xs">
          {error}
        </div>
      )}

      {cases && cases.length === 0 && (
        <Card className="p-8 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto">
            <FileText className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <p className="text-lg font-bold text-slate-900">ابھی کوئی کیس جمع نہیں ہوا</p>
            <p className="text-xs text-slate-500">No applications found. You can apply for a cash relief grant right now.</p>
          </div>
          <div className="pt-2">
            <Link href="/apply">
              <Button variant="primary">نئی درخواست دیں · Apply Now</Button>
            </Link>
          </div>
        </Card>
      )}

      {cases?.map((c) => {
        const meta = STATUS_MAP[c.status] ?? STATUS_MAP.submitted;
        const d = c.decision;
        const isOpen = open === c.id;

        return (
          <Card key={c.id} className="p-5 space-y-3">
            <button
              className="w-full text-start"
              onClick={() => setOpen(isOpen ? "" : c.id)}
              type="button"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <p className="text-base font-bold text-slate-900">{c.citizen_name}</p>
                  <p className="text-xs text-slate-500 font-mono">
                    Case #{c.id.slice(0, 8)} · CNIC: <span dir="ltr">{c.cnic}</span>
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <StatusBadge status={meta.badge} labelUr={meta.ur} labelEn={meta.en} />
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Progress Stepping Bar */}
              <div className="flex gap-1.5 mt-3">
                {[1, 2, 3, 4].map((n) => (
                  <div
                    key={n}
                    className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                      n <= meta.step ? "bg-[#0B4F43]" : "bg-slate-200"
                    }`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[11px] font-medium text-slate-500 mt-1">
                <span className={meta.step >= 1 ? "text-[#0B4F43] font-bold" : ""}>1. جمع</span>
                <span className={meta.step >= 2 ? "text-[#0B4F43] font-bold" : ""}>2. جانچ</span>
                <span className={meta.step >= 3 ? "text-[#0B4F43] font-bold" : ""}>3. فیصلہ</span>
                <span className={meta.step >= 4 ? "text-[#0B4F43] font-bold" : ""}>4. ادائیگی</span>
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-slate-100 pt-3 space-y-3 text-xs">
                <div className="bg-slate-50 rounded-xl p-3.5 space-y-1.5 border border-slate-200">
                  <p className="flex justify-between">
                    <span className="text-slate-500">مطلوبہ رقم · Amount:</span>
                    <span className="font-mono font-bold text-slate-900">Rs {c.requested_amount.toLocaleString()}</span>
                  </p>
                  <p className="flex justify-between">
                    <span className="text-slate-500">تاریخ جمع · Submitted:</span>
                    <span className="text-slate-700">{new Date(c.created_at).toLocaleString()}</span>
                  </p>
                  {c.disbursement_ref && (
                    <p className="flex justify-between text-emerald-800 font-medium pt-1 border-t border-slate-200">
                      <span>Raast Reference:</span>
                      <span className="font-mono font-bold">{c.disbursement_ref}</span>
                    </p>
                  )}
                </div>

                {d ? (
                  <div className={`rounded-xl p-4 border space-y-2 ${
                    d.route === "auto_approve"
                      ? "bg-emerald-50 border-emerald-200 text-emerald-950"
                      : d.route === "ask_more_proof"
                      ? "bg-amber-50 border-amber-200 text-amber-950"
                      : "bg-indigo-50 border-indigo-200 text-indigo-950"
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs uppercase tracking-wide">
                        {d.route === "auto_approve" ? "منظور شدہ · Approved" : d.route === "ask_more_proof" ? "مزید ثبوت درکار · Proof Needed" : "افسر کے پاس زیرِ جائزہ · Under Review"}
                      </span>
                      <button
                        onClick={() => speak(d.reason_simple.ur, "ur-PK")}
                        type="button"
                        className="p-1.5 rounded-lg bg-white/80 hover:bg-white text-slate-700 text-xs flex items-center gap-1 shadow-sm"
                        aria-label="Listen reason"
                      >
                        <Volume2 className="w-3.5 h-3.5" /> سنیں
                      </button>
                    </div>

                    <p className="font-bold text-sm leading-snug">{d.reason_simple.ur}</p>
                    <p className="text-xs text-slate-600">{d.reason_simple.en}</p>

                    {d.missing.length > 0 && (
                      <div className="bg-white/80 rounded-lg p-2.5 border border-current space-y-1">
                        <span className="font-semibold block">مطلوبہ اضافی دستاویز:</span>
                        <ul className="list-disc ps-4 space-y-0.5">
                          {d.missing.map((m) => <li key={m}>{m}</li>)}
                        </ul>
                        <div className="pt-1">
                          <Link href="/documents" className="font-bold text-[#0B4F43] hover:underline inline-flex items-center gap-1">
                            کاغذ اپ لوڈ کریں · Upload <ArrowRight className="w-3 h-3 rtl:rotate-180" />
                          </Link>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    فیصلے کا انتظار ہے · Awaiting evaluation
                  </p>
                )}

                {c.officer_notes && (
                  <div className="bg-white rounded-lg border border-slate-200 p-3 space-y-1">
                    <span className="font-bold text-[#0B4F43] block">افسر کا تحریری نوٹ · Officer Note:</span>
                    <p className="text-slate-800 leading-relaxed">{c.officer_notes}</p>
                  </div>
                )}
              </div>
            )}
          </Card>
        );
      })}
    </AppShell>
  );
}
