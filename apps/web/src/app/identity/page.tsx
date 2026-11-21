"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, WifiOff } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type NadraResult } from "@/lib/api";

const PRESETS = [
  { label: "Muhammad vs Mohammad", cnic: "42101-7654321-2", name: "Muhammad Tariq" },
  { label: "Spelling slip", cnic: "42101-7654321-2", name: "Mohamad Tarik" },
  { label: "Urdu name", cnic: "42101-1234567-1", name: "پروین بی بی" },
  { label: "Wrong name", cnic: "42101-1234567-1", name: "Ahmed Raza" },
  { label: "CNIC not found", cnic: "42101-0000000-0", name: "Ali Khan" },
  { label: "Deceased record", cnic: "42301-5555555-5", name: "Deceased Record Test" },
];

function verdict(r: NadraResult) {
  if (r.deceased)
    return { tone: "bg-red-100 text-red-900", icon: <XCircle className="w-12 h-12" />, ur: "یہ ریکارڈ فوت شدہ شخص کا ہے", en: "Record belongs to a deceased person. Sent to an officer (possible fraud)." };
  if (r.status === "RECORD_NOT_FOUND")
    return { tone: "bg-amber-100 text-amber-900", icon: <AlertTriangle className="w-12 h-12" />, ur: "ریکارڈ نہیں ملا", en: "No record for this CNIC. Ask for another ID or send to an officer." };
  if (r.matched && r.match_score >= 0.9)
    return { tone: "bg-emerald-100 text-emerald-900", icon: <CheckCircle2 className="w-12 h-12" />, ur: "نام ایک ہی شخص کا ہے", en: "Same person. The difference is only a spelling variant." };
  if (r.matched)
    return { tone: "bg-amber-100 text-amber-900", icon: <AlertTriangle className="w-12 h-12" />, ur: "غالباً وہی شخص، افسر تصدیق کرے", en: "Probably the same person. An officer should confirm." };
  return { tone: "bg-red-100 text-red-900", icon: <XCircle className="w-12 h-12" />, ur: "نام نہیں ملتا", en: "Name does not match. An officer reviews it. The citizen is never auto-rejected." };
}

export default function IdentityPage() {
  const [cnic, setCnic] = useState("");
  const [name, setName] = useState("");
  const [chaos, setChaos] = useState("none");
  const [res, setRes] = useState<NadraResult | null>(null);
  const [down, setDown] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(c = cnic, n = name) {
    setBusy(true); setRes(null); setDown(null);
    try { setRes(await api.verifyIdentity(c, n, chaos)); }
    catch (e) { setDown(e as ApiError); }
    finally { setBusy(false); }
  }

  const v = res ? verdict(res) : null;
  return (
    <AppShell title="شناخت جانچ · Identity Check">
      <p className="text-gray-600">Names are spelled many ways (Muhammad, Mohammad, Mohd). The system compares them by <b>similarity</b>, not exact letters. NADRA here is a simulation.</p>

      <div className="flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => { setCnic(p.cnic); setName(p.name); run(p.cnic, p.name); }} className="h-11 px-4 rounded-full bg-emerald-100 text-emerald-800 font-bold text-sm">
            {p.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-3">
        <input className="w-full h-14 border-2 rounded-2xl px-4 text-lg" placeholder="CNIC 42101-1234567-1" inputMode="numeric" value={cnic} onChange={(e) => setCnic(e.target.value)} />
        <input className="w-full h-14 border-2 rounded-2xl px-4 text-lg" placeholder="Name on the form / فارم پر نام" value={name} onChange={(e) => setName(e.target.value)} />
        <label className="flex items-center gap-2 text-sm">
          Simulate NADRA problem:
          <select className="border-2 rounded-xl h-10 px-2" value={chaos} onChange={(e) => setChaos(e.target.value)}>
            <option value="none">None</option><option value="timeout">Timeout</option><option value="500">Server error</option><option value="slow">Slow</option>
          </select>
        </label>
        <button onClick={() => run()} disabled={busy || !cnic || !name} className="w-full h-14 rounded-2xl bg-emerald-600 text-white text-lg font-bold disabled:opacity-40">
          {busy ? "..." : "جانچیں · Verify"}
        </button>
      </div>

      {down && (
        <div className="rounded-3xl p-5 bg-sky-100 text-sky-900 flex gap-4 items-start">
          <WifiOff className="w-12 h-12 shrink-0" />
          <div>
            <p className="text-xl font-bold">نادرا دستیاب نہیں · NADRA is unavailable</p>
            <p>{down.message_en ?? "Service error"}</p>
            <p className="font-bold mt-1">The case waits and is retried later. The citizen is NOT rejected.</p>
          </div>
        </div>
      )}

      {res && v && (
        <div className={`rounded-3xl p-5 space-y-3 ${v.tone}`}>
          <div className="flex items-center gap-4">{v.icon}<div><p className="text-2xl font-bold">{v.ur}</p><p>{v.en}</p></div></div>
          <div className="grid grid-cols-2 gap-3 bg-white/60 rounded-2xl p-3 text-center">
            <div><p className="text-sm text-gray-600">You typed</p><p className="font-bold">{name}</p></div>
            <div><p className="text-sm text-gray-600">Official record</p><p className="font-bold">{res.canonical_name}</p></div>
          </div>
          <div>
            <div className="flex justify-between text-sm"><span>Name similarity</span><b>{Math.round(res.match_score * 100)}%</b></div>
            <div className="h-4 bg-white/70 rounded-full overflow-hidden relative">
              <div className="h-full bg-emerald-600" style={{ width: `${res.match_score * 100}%` }} />
              <div className="absolute top-0 bottom-0 w-0.5 bg-red-600" style={{ insetInlineStart: "70%" }} title="match threshold 70%" />
            </div>
            <p className="text-xs mt-1">Red line = 70% match threshold · Status: {res.status} · {res.latency_ms} ms</p>
          </div>
        </div>
      )}
    </AppShell>
  );
}