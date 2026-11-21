"use client";

import { useEffect, useState } from "react";
import { FlaskConical, Rocket } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type RuleSet, type RuleVersion, type SimulationResult } from "@/lib/api";

export default function AdminPage() {
  const [active, setActive] = useState<RuleSet | null>(null);
  const [draft, setDraft] = useState<RuleSet | null>(null);
  const [versions, setVersions] = useState<RuleVersion[]>([]);
  const [sim, setSim] = useState<SimulationResult | null>(null);
  const [simulatedFor, setSimulatedFor] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [a, v] = await Promise.all([api.getActiveRules(), api.listRuleVersions()]);
      setActive(a); setDraft(a); setVersions(v);
    } catch (e) {
      setError((e as ApiError).message_en ?? "Could not load rules");
    }
  }
  useEffect(() => { load(); }, []);

  if (!active || !draft) return <AppShell title="قواعد · Rules">{error && <p className="text-red-600 font-bold">{error}</p>}</AppShell>;

  const draftKey = JSON.stringify(draft);
  const canPublish = sim !== null && simulatedFor === draftKey && draftKey !== JSON.stringify(active);
  const set = <K extends keyof RuleSet>(k: K, v: RuleSet[K]) => setDraft({ ...draft, [k]: v });
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

  async function simulate() {
    setBusy(true); setError(""); setMsg("");
    try { setSim(await api.simulateRules(draft!, 100)); setSimulatedFor(draftKey); }
    catch (e) { setError((e as ApiError).message_en ?? "Simulation failed"); }
    finally { setBusy(false); }
  }
  async function publish() {
    setBusy(true); setError("");
    try {
      const p = await api.publishRule(draft!);
      setMsg(`Published as version v${p.version}. New decisions use it immediately, no restart needed.`);
      setSim(null);
      await load();
    } catch (e) { setError((e as ApiError).message_en ?? "Publish failed"); }
    finally { setBusy(false); }
  }

  const num = "w-full h-14 border-2 rounded-2xl px-4 text-lg bg-white";
  return (
    <AppShell title="قواعد · Rule Editor">
      <p className="text-gray-600">Active rule set: <b>v{active.version} · {active.name}</b>. Change a value, test it on 100 past cases, then publish.</p>
      {msg && <p className="bg-emerald-100 text-emerald-800 rounded-2xl p-3 font-bold">{msg}</p>}
      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

      <div className="bg-white rounded-3xl shadow p-5 space-y-4">
        <label className="block">
          <span className="font-bold">زیادہ سے زیادہ ماہانہ آمدنی · Max monthly income (Rs)</span>
          <div className="flex gap-2 mt-1">
            <button onClick={() => set("max_monthly_income", Math.max(0, draft.max_monthly_income - 1000))} className="h-14 w-14 rounded-2xl bg-emerald-100 text-2xl font-bold">−</button>
            <input className={num} type="number" value={draft.max_monthly_income} onChange={(e) => set("max_monthly_income", Number(e.target.value))} />
            <button onClick={() => set("max_monthly_income", draft.max_monthly_income + 1000)} className="h-14 w-14 rounded-2xl bg-emerald-100 text-2xl font-bold">+</button>
          </div>
        </label>
        <label className="block">
          <span className="font-bold">خودکار منظوری کی حد · Auto-approve up to (Rs)</span>
          <input className={`${num} mt-1`} type="number" value={draft.max_auto_approve_amount} onChange={(e) => set("max_auto_approve_amount", Number(e.target.value))} />
        </label>
        <label className="block">
          <span className="font-bold">کم از کم گھرانہ · Minimum household size</span>
          <input className={`${num} mt-1`} type="number" value={draft.min_household_size} onChange={(e) => set("min_household_size", Number(e.target.value))} />
        </label>
        <label className="flex items-center gap-3 font-bold">
          <input type="checkbox" className="w-6 h-6" checked={draft.requires_utility_bill} onChange={(e) => set("requires_utility_bill", e.target.checked)} />
          بجلی کا بل لازمی · Utility bill required
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3 font-bold">
        <button onClick={simulate} disabled={busy || draftKey === JSON.stringify(active)} className="h-14 rounded-2xl bg-sky-600 text-white inline-flex items-center justify-center gap-2 disabled:opacity-40">
          <FlaskConical className="w-5 h-5" /> Test · آزمائیں
        </button>
        <button onClick={publish} disabled={busy || !canPublish} className="h-14 rounded-2xl bg-emerald-700 text-white inline-flex items-center justify-center gap-2 disabled:opacity-40">
          <Rocket className="w-5 h-5" /> Publish · شائع
        </button>
      </div>
      {!canPublish && <p className="text-sm text-gray-500">You must test the exact change before you can publish it.</p>}

      {sim && (
        <div className="bg-white rounded-3xl shadow p-5 space-y-3">
          <p className="text-xl font-bold">Digital Twin — v{sim.previous_rule_version} → v{sim.draft_rule_version}</p>
          {[["Before", sim.previous_approval_rate, "bg-gray-400"], ["After", sim.projected_approval_rate, "bg-emerald-500"]].map(([label, val, color]) => (
            <div key={label as string}>
              <div className="flex justify-between text-sm"><span>{label as string} approval rate</span><b>{pct(val as number)}</b></div>
              <div className="h-5 bg-gray-200 rounded-full overflow-hidden"><div className={`h-full ${color}`} style={{ width: `${(val as number) * 100}%` }} /></div>
            </div>
          ))}
          <p className={`text-lg font-bold ${sim.approval_rate_delta >= 0 ? "text-emerald-700" : "text-red-700"}`}>
            Change: {sim.approval_rate_delta >= 0 ? "+" : ""}{pct(sim.approval_rate_delta)}
          </p>
          <p>{sim.impact_summary}</p>
          <p className="text-sm text-gray-500">Tested on {sim.total_cases_simulated} sample cases · {sim.affected_case_ids.length} cases change outcome</p>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow p-5">
        <p className="font-bold mb-2">Version history</p>
        {[...versions].reverse().map((v) => (
          <p key={v.version} className="flex justify-between border-b py-1 text-sm">
            <span>v{v.version} · {v.name} · limit Rs {v.rule_set.max_monthly_income}</span>
            {v.is_active && <b className="text-emerald-700">ACTIVE</b>}
          </p>
        ))}
      </div>
    </AppShell>
  );
}