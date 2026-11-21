"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, XCircle, FileQuestion } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ReviewQueueItem } from "@/lib/api";

const LABELS: Record<string, string> = {
  identity: "Identity", ocr: "Document reading", authenticity: "Authenticity",
  rules_complete: "Rules complete", scam_safety: "Scam safety",
};

export default function OfficerPage() {
  const [items, setItems] = useState<ReviewQueueItem[] | null>(null);
  const [open, setOpen] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

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
    if (notes.trim().length < 10) { setError("Notes must be at least 10 characters (audit rule). نوٹ کم از کم 10 حروف"); return; }
    setBusy(true); setError("");
    try {
      await api.decideReview(caseId, decision, approved, notes.trim());
      setMsg(`Case ${caseId}: decision saved and written to the audit log.`);
      setNotes(""); setOpen("");
      await load();
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not save the decision");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="ریویو قطار · Review Queue">
      <p className="text-gray-600">Lowest-confidence and highest-priority cases are first. The system never rejects on its own.</p>
      {msg && <p className="bg-emerald-100 text-emerald-800 rounded-2xl p-3 font-bold">{msg}</p>}
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}
      {items && items.length === 0 && <p className="bg-white rounded-3xl p-6 text-center text-xl font-bold">قطار خالی ہے · Queue is empty ✓</p>}

      {items?.map((it) => (
        <div key={it.case_id} className="bg-white rounded-3xl shadow p-5 space-y-3">
          <button className="w-full text-start" onClick={() => { setOpen(open === it.case_id ? "" : it.case_id); setError(""); }}>
            <div className="flex justify-between items-center gap-2">
              <p className="text-lg font-bold">{it.citizen_name}</p>
              <span className="px-3 rounded-full bg-amber-100 text-amber-900 font-bold">Priority {it.priority_score.toFixed(1)}</span>
            </div>
            <p className="text-sm text-gray-500">{it.cnic} · Rs {it.requested_amount} · Confidence {Math.round(it.confidence * 100)}%</p>
          </button>

          {open === it.case_id && (
            <div className="border-t pt-3 space-y-3">
              <div>
                <p className="font-bold">Why it needs a human</p>
                <ul className="list-disc ps-6">{it.handoff_packet.flags.map((f) => <li key={f}>{f}</li>)}</ul>
              </div>
              <p className="bg-emerald-50 rounded-xl p-3"><b>Suggested:</b> {it.handoff_packet.suggested_action}</p>
              <div className="space-y-1">
                {Object.entries(it.handoff_packet.component_breakdown).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-2 text-sm">
                    <span className="w-36">{LABELS[k] ?? k}</span>
                    <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div className={`h-full ${v < 0.6 ? "bg-red-500" : "bg-emerald-500"}`} style={{ width: `${v * 100}%` }} />
                    </div>
                    <span className="w-10 text-end">{Math.round(v * 100)}</span>
                  </div>
                ))}
              </div>
              <textarea
                className="w-full h-24 border-2 rounded-2xl p-3 bg-white"
                placeholder="Mandatory notes (min 10 characters) / لازمی نوٹ"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
              <div className="grid grid-cols-3 gap-2 font-bold text-white">
                <button disabled={busy} onClick={() => decide(it.case_id, "auto_approve", true)} className="h-14 rounded-2xl bg-emerald-600 inline-flex items-center justify-center gap-1 disabled:opacity-50">
                  <CheckCircle2 className="w-5 h-5" /> Approve
                </button>
                <button disabled={busy} onClick={() => decide(it.case_id, "ask_more_proof", false)} className="h-14 rounded-2xl bg-amber-600 inline-flex items-center justify-center gap-1 disabled:opacity-50">
                  <FileQuestion className="w-5 h-5" /> More proof
                </button>
                <button disabled={busy} onClick={() => decide(it.case_id, "human_review", false)} className="h-14 rounded-2xl bg-red-600 inline-flex items-center justify-center gap-1 disabled:opacity-50">
                  <XCircle className="w-5 h-5" /> Reject
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
    </AppShell>
  );
}