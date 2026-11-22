"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, AlertOctagon, FileQuestion, AlertTriangle, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type ReviewQueueItem } from "@/lib/api";

const LABELS: Record<string, { ur: string; en: string }> = {
  identity: { ur: "شناخت و نادرا", en: "Identity / NADRA" },
  ocr: { ur: "دستاویز خوانی", en: "Document OCR" },
  authenticity: { ur: "اصلیت و ٹیمپرنگ", en: "Authenticity" },
  rules_complete: { ur: "پالیسی شرائط", en: "Policy Rules" },
  scam_safety: { ur: "اسکیم سیفٹی", en: "Scam Safety" },
};

export default function OfficerPage() {
  const [items, setItems] = useState<ReviewQueueItem[] | null>(null);
  const [open, setOpen] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [confirmRejectId, setConfirmRejectId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const q = await api.getOfficerQueue();
      setItems([...q].sort((a, b) => b.priority_score - a.priority_score));
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not load the queue");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function decide(caseId: string, decision: string, approved: boolean) {
    if (notes.trim().length < 10) {
      setError("لازمی آڈٹ نوٹ کم از کم 10 حروف ہونا چاہیے · Officer notes must be at least 10 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.decideReview(caseId, decision, approved, notes.trim());
      setMsg(`کیس ${caseId} کا فیصلہ محفوظ ہو گیا اور آڈٹ لاگ میں لکھ دیا گیا · Decision recorded in tamper-proof audit log.`);
      setNotes("");
      setOpen("");
      setConfirmRejectId(null);
      await load();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not save the decision");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="ریویو قطار · Officer Review Queue">
      {/* Zero Auto-Reject Guiding Policy Banner */}
      <Card className="p-5 border-2 border-[#1F8A5B] bg-[#DDEFE9]/30 flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center shrink-0">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <div>
          <p className="font-bold text-[#0B4F43] text-base">زیرو خودکار مسترد پالیسی · Zero Auto-Reject Safety Invariant</p>
          <p className="text-xs text-[#5B6F6A] mt-0.5">
            سسٹم کبھی کسی شہری کو خودکار مسترد نہیں کرتا۔ کم اعتماد والے کیسز انسانی جائزے کے لیے یہاں ترجیحی اسکور کے مطابق ترتیب دیے گئے ہیں۔
          </p>
        </div>
      </Card>

      {msg && <p className="bg-[#DDEFE9] text-[#0B4F43] border border-[#1F8A5B] rounded-2xl p-4 font-bold text-sm shadow-sm">{msg}</p>}
      {error && <p className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] rounded-2xl p-4 font-bold text-sm shadow-sm">{error}</p>}

      {items && items.length === 0 && (
        <Card className="p-8 text-center space-y-3">
          <CheckCircle2 className="w-12 h-12 text-[#1F8A5B] mx-auto" />
          <p className="text-xl font-bold text-[#17302B]">قطار مکمل خالی ہے · Queue is empty</p>
          <p className="text-sm text-[#5B6F6A]">تمام ریلیف کیسز خوش اسلوبی سے نمٹا دیے گئے ہیں۔</p>
        </Card>
      )}

      {items?.map((it) => {
        const isOpen = open === it.case_id;
        const breakdown = it.handoff_packet.component_breakdown || {};
        const entries = Object.entries(breakdown);
        // Weakest link calculation
        const weakest = entries.length > 0
          ? entries.reduce((min, cur) => cur[1] < min[1] ? cur : min, entries[0])
          : null;

        return (
          <Card key={it.case_id} className="p-5 space-y-4">
            <button
              className="w-full text-start flex items-center justify-between gap-3"
              onClick={() => { setOpen(isOpen ? "" : it.case_id); setError(""); setConfirmRejectId(null); }}
              type="button"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="text-lg font-bold text-[#17302B]">{it.citizen_name}</p>
                  <StatusBadge status="in_review" labelUr={`ترجیح ${it.priority_score.toFixed(1)}`} labelEn={`P ${it.priority_score.toFixed(1)}`} />
                </div>
                <p className="text-xs text-[#5B6F6A] font-mono">
                  CNIC: {it.cnic} · Claim: Rs {it.requested_amount.toLocaleString()} · Overall Confidence: {Math.round(it.confidence * 100)}%
                </p>
              </div>
              <div className="text-[#5B6F6A]">
                {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-[#E2DDD3] pt-4 space-y-4 animate-fade-up">
                {/* Weakest Link Callout */}
                {weakest && (
                  <div className="bg-[#FFFBEB] border-2 border-[#E8A33D] rounded-2xl p-4 flex items-center justify-between gap-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#FEF3C7] text-[#C77700] flex items-center justify-center shrink-0">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                      <div>
                        <span className="text-[11px] font-bold text-[#C77700] uppercase tracking-wider block">سب سے کمزور جزو · Weakest Link</span>
                        <p className="font-bold text-sm text-[#17302B]">
                          {LABELS[weakest[0]]?.ur ?? weakest[0]} ({LABELS[weakest[0]]?.en ?? weakest[0]}): <span className="text-[#C77700] font-mono font-bold">{Math.round(weakest[1] * 100)}%</span>
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold bg-[#FEF3C7] text-[#92400E] px-3 py-1 rounded-xl">
                      Requires Review
                    </span>
                  </div>
                )}

                {/* Handoff Packet Flags */}
                <div className="bg-[#F7F4EE] rounded-2xl p-4 border border-[#E2DDD3] space-y-2">
                  <p className="font-bold text-sm text-[#0B4F43]">افسر کے لیے تفصیلات · Handoff Packet Flags</p>
                  <ul className="list-disc ps-5 text-xs text-[#17302B] space-y-1">
                    {it.handoff_packet.flags.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                  <p className="text-xs text-[#5B6F6A] pt-1">
                    <b>تجویز کردہ اقدام · Suggested Action:</b> {it.handoff_packet.suggested_action}
                  </p>
                </div>

                {/* All 5 Component Breakdown Bars */}
                <div className="space-y-2 bg-[#F7F4EE]/60 rounded-2xl p-4 border border-[#E2DDD3]">
                  <p className="text-xs font-bold text-[#5B6F6A] uppercase mb-1">تمام اعتمادی اجزاء · 5-Point Component Breakdown</p>
                  {entries.map(([k, v]) => {
                    const isWeak = weakest && weakest[0] === k;
                    return (
                      <div key={k} className="flex items-center gap-2 text-xs">
                        <span className={`w-40 truncate ${isWeak ? "font-bold text-[#C77700]" : "text-[#17302B]"}`}>
                          {LABELS[k]?.ur ?? k}
                        </span>
                        <div className="flex-1 h-3 bg-[#E2DDD3] rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${v < 0.6 ? "bg-[#C77700]" : "bg-[#1F8A5B]"}`}
                            style={{ width: `${Math.round(v * 100)}%` }}
                          />
                        </div>
                        <span className="w-10 text-end font-mono font-bold">{Math.round(v * 100)}%</span>
                      </div>
                    );
                  })}
                </div>

                {/* Mandatory Officer Notes */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-[#17302B]">
                    لازمی افسر نوٹ (کم از کم 10 حروف) · Mandatory Written Reason (min 10 characters)
                  </label>
                  <textarea
                    className="w-full min-h-[90px] border-2 border-[#E2DDD3] rounded-2xl p-3 text-sm bg-white text-[#17302B] focus:border-[#0F6B5A] focus:outline-none transition"
                    placeholder="فیصلے کی ٹھوس وجہ یہاں درج کریں... / Record official justification for audit..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>

                {/* Rejection Confirmation Step */}
                {confirmRejectId === it.case_id ? (
                  <div className="bg-[#FFFBEB] border-2 border-[#5B6F6A] rounded-2xl p-4 space-y-3">
                    <p className="font-bold text-sm text-[#17302B]">
                      کیا آپ واقعی اس کیس کو مسترد کرنا چاہتے ہیں؟ · Confirm Rejection
                    </p>
                    <p className="text-xs text-[#5B6F6A]">
                      مسترد کرنے پر تحریری وجہ آڈٹ لاگ میں محفوظ ہوگی اور شہری کو مطلع کیا جائے گا۔
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="neutral"
                        onClick={() => setConfirmRejectId(null)}
                        className="flex-1"
                      >
                        منسوخ کریں · Cancel
                      </Button>
                      <Button
                        variant="neutral"
                        disabled={busy}
                        onClick={() => decide(it.case_id, "human_review", false)}
                        className="flex-1 bg-[#5B6F6A] text-white hover:bg-[#475753]"
                      >
                        {busy ? "محفوظ ہو رہا ہے..." : "ہاں، مسترد کریں · Confirm Reject"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* 3 Action Buttons */
                  <div className="grid grid-cols-3 gap-2 font-bold text-sm pt-1">
                    {/* 1. Approve (Positive Style: #1F8A5B) */}
                    <Button
                      variant="secondary"
                      disabled={busy}
                      onClick={() => decide(it.case_id, "auto_approve", true)}
                      className="bg-[#1F8A5B] hover:bg-[#187049]"
                    >
                      <CheckCircle2 className="w-4 h-4" /> منظور · Approve
                    </Button>

                    {/* 2. Ask More Proof (Warm Accent Style: #E8A33D) */}
                    <Button
                      variant="primary"
                      disabled={busy}
                      onClick={() => decide(it.case_id, "ask_more_proof", false)}
                    >
                      <FileQuestion className="w-4 h-4" /> ثبوت · Proof
                    </Button>

                    {/* 3. Reject (Neutral Outlined Style: NOT RED) */}
                    <Button
                      variant="neutral"
                      disabled={busy}
                      onClick={() => {
                        if (notes.trim().length < 10) {
                          setError("مسترد کرنے سے پہلے تحریری نوٹ درج کرنا لازمی ہے۔");
                          return;
                        }
                        setConfirmRejectId(it.case_id);
                      }}
                      className="border-[#5B6F6A] text-[#17302B]"
                    >
                      <AlertOctagon className="w-4 h-4 text-[#5B6F6A]" /> مسترد · Reject
                    </Button>
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
