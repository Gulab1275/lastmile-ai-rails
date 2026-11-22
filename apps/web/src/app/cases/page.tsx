"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Volume2, ChevronDown, ChevronUp, FileText, CheckCircle2, AlertTriangle, HelpCircle } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type CaseItem, type CaseStatus } from "@/lib/api";
import { getSession, speak } from "@/lib/session";

const LOOK: Record<CaseStatus, { ur: string; en: string; step: number; color: string; bg: string }> = {
  draft: { ur: "مسودہ", en: "Draft", step: 1, color: "text-[#5B6F6A]", bg: "bg-[#E2DDD3]" },
  submitted: { ur: "جمع ہو گئی", en: "Submitted", step: 1, color: "text-[#0369A1]", bg: "bg-[#E0F2FE]" },
  processing: { ur: "کارروائی جاری", en: "Processing", step: 2, color: "text-[#0369A1]", bg: "bg-[#E0F2FE]" },
  in_review: { ur: "افسر دیکھ رہا ہے", en: "With Officer", step: 2, color: "text-[#4C5FD5]", bg: "bg-[#EEF2FF]" },
  need_proof: { ur: "مزید ثبوت چاہیے", en: "Proof Needed", step: 2, color: "text-[#92400E]", bg: "bg-[#FEF3C7]" },
  need_more_info: { ur: "معلومات چاہیے", en: "Info Needed", step: 2, color: "text-[#92400E]", bg: "bg-[#FEF3C7]" },
  approved: { ur: "منظور", en: "Approved", step: 3, color: "text-[#0B4F43]", bg: "bg-[#DDEFE9]" },
  disbursed: { ur: "رقم ادا ہو گئی", en: "Disbursed", step: 4, color: "text-[#0B4F43]", bg: "bg-[#DDEFE9]" },
  rejected: { ur: "مسترد", en: "Officer Declined", step: 3, color: "text-[#5B6F6A]", bg: "bg-slate-200" },
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
      {error && <p className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] rounded-2xl p-4 font-bold text-sm">{error}</p>}

      {cases && cases.length === 0 && (
        <div className="bg-white rounded-3xl p-8 text-center space-y-3 border border-[#E2DDD3]">
          <FileText className="w-12 h-12 text-[#5B6F6A] mx-auto" />
          <p className="text-xl font-bold text-[#17302B]">ابھی کوئی کیس جمع نہیں ہوا · No cases yet</p>
          <p className="text-xs text-[#5B6F6A]">آپ ابھی نئی ریلیف گرانٹ کی درخواست جمع کرا سکتے ہیں۔</p>
          <div className="pt-2">
            <Link href="/apply" className="inline-block min-h-[48px] px-6 leading-[48px] rounded-2xl bg-[#0B4F43] text-white font-bold text-sm">
              نئی درخواست دیں · Apply Now
            </Link>
          </div>
        </div>
      )}

      {cases?.map((c) => {
        const look = LOOK[c.status] ?? LOOK.submitted;
        const d = c.decision;
        const isOpen = open === c.id;
        return (
          <div key={c.id} className="bg-white rounded-3xl shadow border border-[#E2DDD3] p-5 space-y-3">
            <button
              className="w-full text-start"
              onClick={() => setOpen(isOpen ? "" : c.id)}
              type="button"
            >
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-lg font-bold text-[#17302B]">{c.citizen_name}</p>
                  <p className="text-xs text-[#5B6F6A] font-mono">Case #{c.id.slice(0, 8)} · CNIC: {c.cnic}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full font-bold text-xs ${look.bg} ${look.color}`}>
                    {look.ur} · {look.en}
                  </span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-[#5B6F6A]" /> : <ChevronDown className="w-4 h-4 text-[#5B6F6A]" />}
                </div>
              </div>

              {/* Progress Milestones Bar */}
              <div className="flex gap-1.5 mt-3">
                {[1, 2, 3, 4].map((n) => (
                  <div
                    key={n}
                    className={`h-2 flex-1 rounded-full transition-all ${
                      n <= look.step ? "bg-[#0B4F43]" : "bg-[#E2DDD3]"
                    }`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[10px] font-bold text-[#5B6F6A] mt-1">
                <span>1. جمع</span>
                <span>2. جانچ</span>
                <span>3. فیصلہ</span>
                <span>4. رقم کی ادائیگی</span>
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-[#E2DDD3] pt-3 space-y-3 text-sm animate-fade-up">
                <div className="bg-[#F7F4EE] rounded-2xl p-3 text-xs space-y-1">
                  <p><b>مطلوبہ گرانٹ · Requested Amount:</b> Rs {c.requested_amount.toLocaleString()}</p>
                  <p><b>تاریخ · Submitted:</b> {new Date(c.created_at).toLocaleString()}</p>
                  {c.disbursement_ref && (
                    <p className="font-mono text-[#0B4F43]"><b>Raast Ref:</b> {c.disbursement_ref}</p>
                  )}
                </div>

                {d ? (
                  <div className={`rounded-2xl p-4 border space-y-2 ${
                    d.route === "auto_approve"
                      ? "bg-[#DDEFE9] border-[#1F8A5B] text-[#065F46]"
                      : d.route === "ask_more_proof"
                      ? "bg-[#FEF3C7] border-[#C77700] text-[#92400E]"
                      : "bg-[#EEF2FF] border-[#4C5FD5] text-[#1E1B4B]"
                  }`}>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {d.route === "auto_approve" && <CheckCircle2 className="w-5 h-5 text-[#1F8A5B]" />}
                        {d.route === "ask_more_proof" && <AlertTriangle className="w-5 h-5 text-[#C77700]" />}
                        {d.route === "human_review" && <HelpCircle className="w-5 h-5 text-[#4C5FD5]" />}
                        <span className="font-bold text-xs uppercase">
                          {d.route === "auto_approve" ? "منظور شدہ · Approved" : d.route === "ask_more_proof" ? "مزید ثبوت مطلوب · Proof Needed" : "افسر کے پاس زیرِ جائزہ · Under Review"}
                        </span>
                      </div>
                      <button
                        onClick={() => speak(d.reason_simple.ur)}
                        type="button"
                        className="min-h-[36px] min-w-[36px] rounded-xl bg-white/80 flex items-center justify-center shadow-sm"
                        aria-label="Listen reason"
                      >
                        <Volume2 className="w-4 h-4" />
                      </button>
                    </div>

                    <p className="font-bold">{d.reason_simple.ur}</p>
                    <p className="text-xs">{d.reason_simple.en}</p>

                    {d.missing.length > 0 && (
                      <div className="text-xs bg-white/70 rounded-xl p-2 border border-current">
                        <span className="font-bold">مطلوبہ اضافی دستاویز:</span>
                        <ul className="list-disc ps-4 mt-0.5">
                          {d.missing.map((m) => <li key={m}>{m}</li>)}
                        </ul>
                      </div>
                    )}
                    <p className="text-[10px] opacity-80 font-mono">
                      اعتماد (Confidence): {Math.round(d.confidence * 100)}% · پالیسی ورژن: v{d.rule_version}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-[#5B6F6A] bg-[#F7F4EE] p-3 rounded-xl">فیصلے کا انتظار ہے · Awaiting evaluation</p>
                )}

                {c.officer_notes && (
                  <div className="bg-white rounded-xl border border-[#E2DDD3] p-3 text-xs space-y-1">
                    <span className="font-bold text-[#0B4F43]">افسر کا تحریری نوٹ · Official Officer Note:</span>
                    <p className="text-[#17302B]">{c.officer_notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </AppShell>
  );
}
