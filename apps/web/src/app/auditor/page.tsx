"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck, ShieldAlert, RefreshCw,
  Search, Lock, Hash, Clock,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import api, { type ApiError, type AuditEntry, type ChainStatus } from "@/lib/api";

export default function AuditorPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [chain, setChain] = useState<ChainStatus | null>(null);
  const [caseId, setCaseId] = useState("");
  const [trace, setTrace] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [tracing, setTracing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getAuditLogs().then(setLogs).catch((e: ApiError) => setError(e.message_ur ?? e.message_en ?? "Could not load logs"));
    api.verifyAuditChain().then(setChain).catch(() => { });
  }, []);

  async function verify() {
    setBusy(true);
    try {
      setChain(await api.verifyAuditChain());
    } finally {
      setBusy(false);
    }
  }

  async function explain() {
    if (!caseId.trim()) return;
    setError("");
    setTrace(null);
    setTracing(true);
    try {
      setTrace(await api.explainCase(caseId.trim(), "auditor"));
    } catch (e) {
      setError((e as ApiError).message_ur ?? (e as ApiError).message_en ?? "Could not load trace");
    } finally {
      setTracing(false);
    }
  }

  return (
    <AppShell title="آڈٹ و کرپٹوگرافک لیجر · Auditor Chain">
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">غیر متبدل آڈٹ ہیش چین · Cryptographic Audit Hash Chain</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          ہر کارروائی (رضامندی کی تبدیلی، افسر کا نوٹ، اور خودکار فیصلے) SHA-256 ہیش چین میں محفوظ ہوتی ہے۔ اگر کوئی ڈیٹا بیس میں ریکارڈ تبدیل کرے تو چین ٹوٹ جاتی ہے۔
        </p>
      </Card>

      {error && (
        <div className="bg-rose-50 text-rose-800 border border-rose-200 rounded-xl p-3.5 font-medium text-xs">
          {error}
        </div>
      )}

      {/* Chain Health Banner */}
      {chain && (
        <div
          className={`rounded-2xl p-5 border flex flex-wrap items-center justify-between gap-4 shadow-sm ${chain.is_valid
            ? "bg-emerald-50 border-emerald-300 text-emerald-950"
            : "bg-rose-50 border-rose-300 text-rose-950"
            }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${chain.is_valid ? "bg-emerald-600 text-white" : "bg-rose-600 text-white"
                }`}
            >
              {chain.is_valid ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
            </div>
            <div className="space-y-0.5">
              <p className="text-base font-bold font-heading leading-tight">
                {chain.is_valid ? "ہیش چین مکمل محفوظ ہے · Cryptographic Chain Intact" : "چھیڑ چھاڑ پکڑی گئی · TAMPERING DETECTED"}
              </p>
              <p className="text-xs opacity-85">
                {chain.total_records} تصدیق شدہ بلاکس (Blocks verified)
                {chain.corrupted_at_index != null && ` · Broken at #${chain.corrupted_at_index}`}
              </p>
              {chain.head_hash && (
                <p className="text-[11px] font-mono opacity-80 break-all" dir="ltr">
                  Head: {chain.head_hash}
                </p>
              )}
            </div>
          </div>

          <Button
            variant="neutral"
            size="sm"
            onClick={verify}
            disabled={busy}
            className="shrink-0"
          >
            {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Verify Chain"}
          </Button>
        </div>
      )}

      {/* Explain Trace */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center gap-2 text-[#0B4F43]">
          <Search className="w-4 h-4" />
          <p className="font-bold text-sm text-slate-900">فیصلے کی تکنیکی تفتیش · Explain Decision Trace</p>
        </div>
        <div className="flex gap-2">
          <input
            className="flex-1 min-h-[44px] border border-slate-300 rounded-xl px-4 text-xs sm:text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
            placeholder="Case ID درج کریں e.g. case-1 or uuid"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={explain}
            disabled={tracing || !caseId.trim()}
          >
            {tracing ? "جانچ ہو رہی ہے..." : "Trace Case"}
          </Button>
        </div>

        {trace && (
          <div className="bg-slate-900 text-emerald-300 rounded-xl p-4 text-xs font-mono space-y-2 overflow-x-auto shadow-inner">
            <p className="text-[11px] font-bold text-emerald-400 border-b border-emerald-800 pb-1">
              DECISION TRACE PACKET (AUDITOR CLEARANCE)
            </p>
            {Object.entries(trace).map(([k, v]) => (
              <div key={k} className="flex gap-2 text-start">
                <span className="font-bold text-emerald-200 w-44 shrink-0">{k}:</span>
                <span className="break-all text-emerald-100">
                  {typeof v === "object" ? JSON.stringify(v, null, 2) : String(v)}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Timeline */}
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <p className="font-bold text-slate-900 text-xs uppercase tracking-wider">ہیش چین ٹائم لائن · Hash Chain Log</p>
          <span className="text-xs text-slate-500">{logs.length} Actions Recorded</span>
        </div>

        <div className="relative border-s-2 border-slate-200 ms-3 ps-5 space-y-4">
          {logs.map((l, i) => (
            <div key={l.id ?? i} className="relative">
              {/* Dot */}
              <div className="absolute -start-[27px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#0B4F43] border-2 border-white shadow-sm" />

              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200 space-y-2 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 text-sm">{l.action}</span>
                    {l.actor_role && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white text-slate-600 border border-slate-200">
                        {l.actor_role}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(l.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-slate-600">
                  <span>Actor: <b>{l.actor ?? "system"}</b></span>
                  {l.resource_id && <span>Resource: <code className="font-mono text-slate-800">{l.resource_id.slice(0, 12)}</code></span>}
                </div>

                <div className="bg-white rounded-lg p-2 border border-slate-200 text-[11px] font-mono text-slate-500 space-y-0.5" dir="ltr">
                  <div className="flex items-center gap-1.5 truncate">
                    <Lock className="w-3 h-3 text-emerald-600 shrink-0" />
                    <span className="text-slate-400">Current:</span>
                    <span className="text-[#0B4F43] font-semibold truncate">{l.current_hash}</span>
                  </div>
                  <div className="flex items-center gap-1.5 truncate opacity-70">
                    <Hash className="w-3 h-3 text-slate-400 shrink-0" />
                    <span className="text-slate-400">Prev:</span>
                    <span className="truncate">{l.prev_hash}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
