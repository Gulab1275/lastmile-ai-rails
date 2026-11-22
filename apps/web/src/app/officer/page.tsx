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
      setMsg(`کیس ${caseId} کا فیصلہ محفوظ ہو گیا اور آڈٹ لاگ میں لکھ دیا گیا · Decision recorded in audit log.`);
      setNotes("");
      setOpen("");
      setConfirmRejectId(null);
      await load();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not save decision");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="ریویو قطار · Officer Review Queue">
      {/* Zero Auto-Reject Banner */}
      <Card className="p-5 border-emerald-300 bg-emerald-50/40 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-100 text-[#0B4F43] flex items-center justify-center shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div className="space-y-0.5">
          <p className="font-bold text-[#0B4F43] text-sm sm:text-base font-heading">
            زیرو خودکار مسترد پالیسی · Zero Auto-Reject Invariant
          </p>
          <p className="text-xs text-slate-600 leading-relaxed">
            کمپیوٹر کبھی کسی ضرورت مند شہری کو خود بخود مسترد نہیں کرتا۔ کم اعتماد والے تمام کیسز انسانی فیصلے کے لیے یہاں آتے ہیں۔
          </p>
        </div>
      </Card>

      {msg && <p className="bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-xl p-3.5 font-medium text-xs">{msg}</p>}
      {error && <p className="bg-rose-50 text-rose-900 border border-rose-200 rounded-xl p-3.5 font-medium text-xs">{error}</p>}

      {items && items.length === 0 && (
        <Card className="p-8 text-center space-y-2">
          <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
          <p className="text-lg font-bold text-slate-900">قطار مکمل خالی ہے · Queue is empty</p>
          <p className="text-xs text-slate-500">تمام ریلیف کیسز نمٹا دیے گئے ہیں۔</p>
        </Card>
      )}

      {items?.map((it) => {
        const isOpen = open === it.case_id;
        const breakdown = it.handoff_packet.component_breakdown || {};
        const entries = Object.entries(breakdown);
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
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <p className="text-base font-bold text-slate-900">{it.citizen_name}</p>
                  <StatusBadge status="in_review" labelUr={`ترجیح ${it.priority_score.toFixed(1)}`} labelEn={`P${it.priority_score.toFixed(1)}`} />
                </div>
                <p className="text-xs text-slate-500 font-mono">
                  CNIC: <span dir="ltr">{it.cnic}</span> · Claim: Rs {it.requested_amount.toLocaleString()} · Overall: {Math.round(it.confidence * 100)}%
                </p>
              </div>
              <div className="text-slate-400">
                {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-slate-100 pt-4 space-y-4 text-xs">
                {/* Weakest Link Callout */}
                {weakest && (
                  <div className="bg-amber-50 border border-amber-300 rounded-xl p-3.5 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0" />
                      <div>
                        <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider block">سب سے کمزور جزو · Weakest Link</span>
                        <p className="font-bold text-xs sm:text-sm text-slate-900">
                          {LABELS[weakest[0]]?.ur ?? weakest[0]}: <span className="text-amber-800 font-mono font-bold">{Math.round(weakest[1] * 100)}%</span>
                        </p>
                      </div>
                    </div>
                    <span className="text-[11px] font-bold bg-amber-200/60 text-amber-900 px-2.5 py-1 rounded">
                      Review Needed
                    </span>
                  </div>
                )}

                {/* Handoff Packet Flags */}
                <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-1.5">
                  <p className="font-bold text-slate-900">افسر کے لیے تفصیلات · Handoff Packet Flags</p>
                  <ul className="list-disc ps-4 space-y-0.5 text-slate-700">
                    {it.handoff_packet.flags.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                  <p className="text-slate-500 pt-1">
                    <b>تجویز کردہ اقدام:</b> {it.handoff_packet.suggested_action}
                  </p>
                </div>

                {/* Component Breakdown Bars */}
                <div className="space-y-2 bg-slate-50 rounded-xl p-3.5 border border-slate-200">
                  <p className="font-bold text-slate-700 uppercase tracking-wider text-[11px] mb-1">
                    تمام اعتمادی اجزاء · 5-Point Component Breakdown
                  </p>
                  {entries.map(([k, v]) => {
                    const isWeak = weakest && weakest[0] === k;
                    return (
                      <div key={k} className="flex items-center gap-2">
                        <span className={`w-36 truncate ${isWeak ? "font-bold text-amber-800" : "text-slate-700"}`}>
                          {LABELS[k]?.ur ?? k}
                        </span>
                        <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${v < 0.6 ? "bg-amber-500" : "bg-emerald-600"}`}
                            style={{ width: `${Math.round(v * 100)}%` }}
                          />
                        </div>
                        <span className="w-10 text-end font-mono font-semibold">{Math.round(v * 100)}%</span>
                      </div>
                    );
                  })}
                </div>

                {/* Mandatory Notes */}
                <div className="space-y-1">
                  <label className="block font-semibold text-slate-700">
                    لازمی تحریری نوٹ (کم از کم 10 حروف) · Mandatory Written Reason
                  </label>
                  <textarea
                    className="w-full min-h-[80px] border border-slate-300 rounded-xl p-3 text-xs bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
                    placeholder="فیصلے کی ٹھوس وجہ یہاں درج کریں... / Record official justification for audit..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                  />
                </div>

                {/* Rejection Confirmation Step */}
                {confirmRejectId === it.case_id ? (
                  <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 space-y-3">
                    <p className="font-bold text-amber-950 text-sm">
                      کیا آپ واقعی اس کیس کو مسترد کرنا چاہتے ہیں؟ · Confirm Rejection
                    </p>
                    <p className="text-slate-600">
                      مسترد کرنے پر تحریری وجہ آڈٹ لاگ میں محفوظ ہوگی اور شہری کو مطلع کیا جائے گا۔
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="neutral"
                        size="sm"
                        onClick={() => setConfirmRejectId(null)}
                        className="flex-1"
                      >
                        منسوخ کریں · Cancel
                      </Button>
                      <Button
                        variant="neutral"
                        size="sm"
                        disabled={busy}
                        onClick={() => decide(it.case_id, "human_review", false)}
                        className="flex-1 bg-slate-700 text-white hover:bg-slate-800"
                      >
                        {busy ? "محفوظ ہو رہا ہے..." : "ہاں، مسترد کریں · Confirm Reject"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* 3 Action Buttons */
                  <div className="grid grid-cols-3 gap-2 pt-1 font-bold">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={busy}
                      onClick={() => decide(it.case_id, "auto_approve", true)}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> منظور · Approve
                    </Button>

                    <Button
                      variant="primary"
                      size="sm"
                      disabled={busy}
                      onClick={() => decide(it.case_id, "ask_more_proof", false)}
                    >
                      <FileQuestion className="w-3.5 h-3.5" /> ثبوت · Proof
                    </Button>

                    <Button
                      variant="neutral"
                      size="sm"
                      disabled={busy}
                      onClick={() => {
                        if (notes.trim().length < 10) {
                          setError("مسترد کرنے سے پہلے تحریری نوٹ درج کرنا لازمی ہے۔");
                          return;
                        }
                        setConfirmRejectId(it.case_id);
                      }}
                      className="border-slate-300 text-slate-800"
                    >
                      <AlertOctagon className="w-3.5 h-3.5 text-slate-500" /> مسترد · Reject
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
