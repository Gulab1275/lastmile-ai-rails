"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck, ShieldAlert, GitCommit, RefreshCw,
  Search, Lock, Hash, Clock,
} from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
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
    api.verifyAuditChain().then(setChain).catch(() => {});
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
      <Card className="p-5 space-y-2">
        <h2 className="text-xl font-bold text-[#0B4F43]">غیر متبدل آڈٹ ہیش چین · Immutable Cryptographic Hash Chain</h2>
        <p className="text-sm text-[#5B6F6A]">
          ہر کارروائی (رضامندی کی تبدیلی، افسر کا نوٹ، اور خودکار فیصلے) SHA-256 ہیش چین میں محفوظ ہوتی ہے۔ اگر کوئی ڈیٹا بیس میں ریکارڈ تبدیل کرے تو چین ٹوٹ جاتی ہے۔
        </p>
      </Card>

      {error && (
        <div className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] rounded-2xl p-4 font-bold text-sm">
          {error}
        </div>
      )}

      {/* Chain Health Status Banner */}
      {chain && (
        <div
          className={`rounded-3xl p-5 border-2 flex items-center justify-between gap-4 shadow-sm transition ${
            chain.is_valid
              ? "bg-[#DDEFE9] border-[#1F8A5B] text-[#065F46]"
              : "bg-[#FEE2E2] border-[#B3261E] text-[#7F1D1D]"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                chain.is_valid ? "bg-[#1F8A5B] text-white" : "bg-[#B3261E] text-white"
              }`}
            >
              {chain.is_valid ? <ShieldCheck className="w-7 h-7" /> : <ShieldAlert className="w-7 h-7" />}
            </div>
            <div>
              <p className="text-lg font-bold leading-tight">
                {chain.is_valid ? "ہیش چین مکمل محفوظ ہے · Cryptographic Chain Intact" : "چھیڑ چھاڑ پکڑی گئی · TAMPERING DETECTED"}
              </p>
              <p className="text-xs opacity-90 mt-0.5">
                {chain.total_records} تصدیق شدہ بلاکس (Blocks verified)
                {chain.corrupted_at_index != null && ` · Broken at block #${chain.corrupted_at_index}`}
              </p>
              {chain.head_hash && (
                <p className="text-[10px] font-mono opacity-80 break-all mt-0.5">
                  Head Hash: {chain.head_hash}
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

      {/* Decision Explainer Trace Tool */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center gap-2 text-[#0B4F43]">
          <Search className="w-5 h-5" />
          <p className="font-bold text-base">فیصلے کی تکنیکی تفتیش · Explain Decision Trace</p>
        </div>
        <p className="text-xs text-[#5B6F6A]">
          کسی بھی کیس کا ID درج کریں تاکہ AI اور رول انجن کے تفصیلی ثبوت اور پیرامیٹرز کا معائنہ کیا جا سکے۔
        </p>
        <div className="flex gap-2">
          <input
            className="flex-1 min-h-[48px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-sm bg-white text-[#17302B] focus:border-[#0F6B5A] focus:outline-none"
            placeholder="Case ID درج کریں e.g. case-1 or uuid"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
          />
          <Button
            variant="secondary"
            onClick={explain}
            disabled={tracing || !caseId.trim()}
          >
            {tracing ? "جانچ ہو رہی ہے..." : "Trace Case"}
          </Button>
        </div>

        {trace && (
          <div className="bg-[#17302B] text-emerald-300 rounded-2xl p-4 text-xs font-mono space-y-2 overflow-x-auto shadow-inner animate-fade-up">
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

      {/* Visual Hash Chain Timeline */}
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#E2DDD3] pb-3">
          <p className="font-bold text-[#0B4F43] text-sm">ہیش چین ٹائم لائن · Hash-Linked Action Log</p>
          <span className="text-xs text-[#5B6F6A] font-bold">{logs.length} Actions Recorded</span>
        </div>

        <div className="relative border-s-2 border-[#0B4F43]/30 ms-4 ps-6 space-y-6">
          {logs.map((l, i) => (
            <div key={l.id ?? i} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -start-[31px] top-1.5 w-4 h-4 rounded-full bg-[#0B4F43] border-2 border-white shadow-sm flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white" />
              </div>

              <div className="bg-[#F7F4EE] rounded-2xl p-4 border border-[#E2DDD3] space-y-2 hover:border-[#0B4F43]/40 transition shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#17302B]">{l.action}</span>
                    {l.actor_role && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white text-[#5B6F6A] border border-[#E2DDD3]">
                        {l.actor_role}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-[#5B6F6A]">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(l.timestamp).toLocaleTimeString()} · {new Date(l.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-[#5B6F6A]">
                  <span>فاعل (Actor): <b>{l.actor ?? "system"}</b></span>
                  {l.resource_id && <span>Resource: <code className="font-mono">{l.resource_id.slice(0, 12)}</code></span>}
                </div>

                {/* Hash Linkage Strip */}
                <div className="bg-white rounded-xl p-2.5 border border-[#E2DDD3] text-[11px] font-mono text-[#5B6F6A] space-y-1">
                  <div className="flex items-center gap-1">
                    <Lock className="w-3 h-3 text-[#1F8A5B] shrink-0" />
                    <span className="text-gray-400">Current:</span>
                    <span className="text-[#0B4F43] font-bold truncate">{l.current_hash}</span>
                  </div>
                  <div className="flex items-center gap-1 opacity-70">
                    <Hash className="w-3 h-3 text-gray-400 shrink-0" />
                    <span className="text-gray-400">Prev:</span>
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
