"use client";

import { useEffect, useState } from "react";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type AuditEntry, type ChainStatus } from "@/lib/api";

export default function AuditorPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [chain, setChain] = useState<ChainStatus | null>(null);
  const [caseId, setCaseId] = useState("");
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getAuditLogs().then(setLogs).catch((e: ApiError) => setError(e.message_en ?? "Could not load logs"));
    api.verifyAuditChain().then(setChain).catch(() => {});
  }, []);

  async function verify() {
    setBusy(true);
    try { setChain(await api.verifyAuditChain()); } finally { setBusy(false); }
  }
  async function explain() {
    setError(""); setTrace(null);
    try { setTrace(await api.explainCase(caseId.trim(), "auditor")); }
    catch (e) { setError((e as ApiError).message_en ?? "Could not load trace"); }
  }

  return (
    <AppShell title="آڈٹ لاگ · Audit Log">
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

      {chain && (
        <div className={`rounded-3xl p-5 flex items-center gap-4 ${chain.is_valid ? "bg-emerald-100 text-emerald-900" : "bg-red-100 text-red-800"}`}>
          {chain.is_valid ? <ShieldCheck className="w-12 h-12" /> : <ShieldAlert className="w-12 h-12" />}
          <div className="flex-1">
            <p className="text-xl font-bold">{chain.is_valid ? "ریکارڈ محفوظ ہے · Chain is intact" : "چھیڑ چھاڑ پکڑی گئی · TAMPERING DETECTED"}</p>
            <p className="text-sm">{chain.total_records} records{chain.corrupted_at_index != null && ` · broken at #${chain.corrupted_at_index}`}</p>
            {chain.head_hash && <p className="text-xs font-mono break-all">head: {chain.head_hash}</p>}
          </div>
          <button onClick={verify} disabled={busy} className="h-12 px-4 rounded-2xl bg-white font-bold">Verify</button>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow p-5 space-y-3">
        <p className="font-bold">Why was this decision made? · فیصلے کی تفصیل</p>
        <div className="flex gap-2">
          <input className="flex-1 h-14 border-2 rounded-2xl px-4" placeholder="Case ID e.g. case-C" value={caseId} onChange={(e) => setCaseId(e.target.value)} />
          <button onClick={explain} disabled={!caseId.trim()} className="h-14 px-5 rounded-2xl bg-emerald-600 text-white font-bold disabled:opacity-40">Trace</button>
        </div>
        {trace && (
          <dl className="bg-emerald-50 rounded-2xl p-3 text-sm space-y-1 overflow-x-auto">
            {Object.entries(trace).map(([k, v]) => (
              <div key={k} className="flex gap-2"><dt className="font-bold w-40 shrink-0">{k}</dt><dd className="font-mono break-all">{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd></div>
            ))}
          </dl>
        )}
      </div>

      <div className="bg-white rounded-3xl shadow p-5 overflow-x-auto">
        <p className="font-bold mb-2">Latest actions</p>
        <table className="w-full text-sm min-w-[520px]">
          <thead><tr className="text-start border-b"><th className="p-1">Time</th><th>Who</th><th>Action</th><th>Resource</th><th>Hash</th></tr></thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={l.id ?? i} className="border-b">
                <td className="p-1">{new Date(l.timestamp).toLocaleTimeString()}</td>
                <td>{l.actor ?? "—"} <span className="text-gray-400">{l.actor_role}</span></td>
                <td className="font-bold">{l.action}</td>
                <td>{l.resource_id ?? "—"}</td>
                <td className="font-mono">{l.current_hash.slice(0, 8)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}