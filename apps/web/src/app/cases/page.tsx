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
  need_proof: { badge: "need_proof", ur: "مزید ثبوت چاہیے", en: "Proof Needed", step: 2 },
  need_more_info: { badge: "need_proof", ur: "معلومات چاہیے", en: "Info Needed", step: 2 },
  approved: { badge: "approved", ur: "منظور", en: "Approved", step: 3 },
  disbursed: { badge: "disbursed", ur: "رقم ادا ہو گئی", en: "Disbursed", step: 4 },
  rejected: { badge: "need_proof", ur: "مسترد", en: "Officer Declined", step: 3 },
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
        <div className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] rounded-2xl p-4 font-bold text-sm">
          {error}
        </div>
      )}

      {cases && cases.length === 0 && (
        <Card className="p-8 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <div>
            <p className="text-xl font-bold text-[#17302B]">ابھی کوئی کیس جمع نہیں ہوا</p>
            <p className="text-xs text-[#5B6F6A] mt-1">No applications submitted yet. You can apply for a cash grant right now.</p>
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
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-lg font-bold text-[#17302B]">{c.citizen_name}</p>
                  <p className="text-xs text-[#5B6F6A] font-mono">
                    Case #{c.id.slice(0, 8)} · CNIC: {c.cnic}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={meta.badge} labelUr={meta.ur} labelEn={meta.en} />
                  {isOpen ? (
                    <ChevronUp className="w-5 h-5 text-[#5B6F6A]" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-[#5B6F6A]" />
                  )}
                </div>
              </div>

              {/* Progress Stepping Bar */}
              <div className="flex gap-1.5 mt-3">
                {[1, 2, 3, 4].map((n) => (
                  <div
                    key={n}
                    className={`h-2 flex-1 rounded-full transition-all duration-300 ${
                      n <= meta.step ? "bg-[#0B4F43]" : "bg-[#E2DDD3]"
                    }`}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[10px] font-bold text-[#5B6F6A] mt-1">
                <span className={meta.step >= 1 ? "text-[#0B4F43]" : ""}>1. جمع (Submit)</span>
                <span className={meta.step >= 2 ? "text-[#0B4F43]" : ""}>2. جانچ (Check)</span>
                <span className={meta.step >= 3 ? "text-[#0B4F43]" : ""}>3. فیصلہ (Decision)</span>
                <span className={meta.step >= 4 ? "text-[#0B4F43]" : ""}>4. ادائیگی (Disburse)</span>
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-[#E2DDD3] pt-3 space-y-3 text-sm animate-fade-up">
                <div className="bg-[#F7F4EE] rounded-2xl p-4 text-xs space-y-1.5 border border-[#E2DDD3]">
                  <p><b>مطلوبہ گرانٹ · Requested Amount:</b> Rs {c.requested_amount.toLocaleString()}</p>
                  <p><b>جمع کرانے کی تاریخ · Submitted:</b> {new Date(c.created_at).toLocaleString()}</p>
                  {c.disbursement_ref && (
                    <div className="flex items-center gap-1.5 text-[#0B4F43] font-bold pt-1">
                      <ShieldCheck className="w-4 h-4 text-[#1F8A5B]" />
                      <span>Raast Reference: <span className="font-mono">{c.disbursement_ref}</span></span>
                    </div>
                  )}
                </div>

                {d ? (
                  <div className={`rounded-2xl p-4 border space-y-2.5 ${
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
                        onClick={() => speak(d.reason_simple.ur, "ur-PK")}
                        type="button"
                        className="min-h-[36px] min-w-[36px] rounded-xl bg-white/80 flex items-center justify-center shadow-sm hover:bg-white transition"
                        aria-label="Listen reason"
                      >
                        <Volume2 className="w-4 h-4" />
                      </button>
                    </div>

                    <p className="font-bold text-base leading-snug">{d.reason_simple.ur}</p>
                    <p className="text-xs opacity-90">{d.reason_simple.en}</p>

                    {d.missing.length > 0 && (
                      <div className="text-xs bg-white/80 rounded-xl p-3 border border-current space-y-1">
                        <span className="font-bold block">مطلوبہ اضافی دستاویز (Missing Documents):</span>
                        <ul className="list-disc ps-4 space-y-0.5">
                          {d.missing.map((m) => <li key={m}>{m}</li>)}
                        </ul>
                        <div className="pt-1">
                          <Link href="/documents" className="inline-flex items-center gap-1 font-bold text-[#0B4F43] hover:underline">
                            کاغذ اپ لوڈ کریں · Upload missing proof <ArrowRight className="w-3 h-3 rtl:rotate-180" />
                          </Link>
                        </div>
                      </div>
                    )}

                    <div className="flex justify-between items-center text-[10px] opacity-80 font-mono pt-1">
                      <span>اعتماد (Confidence): {Math.round(d.confidence * 100)}%</span>
                      <span>پالیسی ورژن: v{d.rule_version}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-[#5B6F6A] bg-[#F7F4EE] p-3 rounded-xl border border-[#E2DDD3]">
                    فیصلے کا انتظار ہے · Awaiting evaluation
                  </p>
                )}

                {c.officer_notes && (
                  <div className="bg-white rounded-xl border border-[#E2DDD3] p-3 text-xs space-y-1 shadow-sm">
                    <span className="font-bold text-[#0B4F43] block">افسر کا تحریری نوٹ · Official Officer Note:</span>
                    <p className="text-[#17302B]">{c.officer_notes}</p>
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
