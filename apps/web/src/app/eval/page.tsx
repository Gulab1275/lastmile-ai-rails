"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import api, { type ApiError, type EvalSummary } from "@/lib/api";

function CostChart({ data, best }: { data: EvalSummary["threshold_sweep_curve"]; best: number }) {
  const W = 600, H = 260, P = 40;
  const xs = data.map((d) => d.threshold);
  const ys = data.map((d) => d.expected_cost_per_case);
  const [x0, x1, y1] = [Math.min(...xs), Math.max(...xs), Math.max(...ys) * 1.1 || 1];
  const sx = (x: number) => P + ((x - x0) / (x1 - x0 || 1)) * (W - 2 * P);
  const sy = (y: number) => H - P - (y / y1) * (H - 2 * P);
  const line = data.map((d) => `${sx(d.threshold)},${sy(d.expected_cost_per_case)}`).join(" ");
  const bestPt = data.find((d) => d.threshold === best);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ direction: "ltr" }} role="img" aria-label="Expected cost vs threshold">
      <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#9ca3af" />
      <line x1={P} y1={P} x2={P} y2={H - P} stroke="#9ca3af" />
      <polyline points={line} fill="none" stroke="#059669" strokeWidth={3} />
      {data.map((d) => <circle key={d.threshold} cx={sx(d.threshold)} cy={sy(d.expected_cost_per_case)} r={4} fill="#059669" />)}
      {bestPt && <circle cx={sx(bestPt.threshold)} cy={sy(bestPt.expected_cost_per_case)} r={9} fill="none" stroke="#dc2626" strokeWidth={3} />}
      <text x={W / 2} y={H - 8} textAnchor="middle" fontSize={12}>Allowed chance of a wrong approval (threshold)</text>
      <text x={12} y={H / 2} fontSize={12} transform={`rotate(-90 12 ${H / 2})`} textAnchor="middle">Expected cost per case</text>
      {[x0, best, x1].map((t) => <text key={t} x={sx(t)} y={H - P + 14} textAnchor="middle" fontSize={11}>{t}</text>)}
    </svg>
  );
}

export default function EvalPage() {
  const [d, setD] = useState<EvalSummary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.getEvalSummary().then(setD).catch((e: ApiError) => setError(e.message_en ?? "Could not load")); }, []);

  if (!d) return <AppShell title="اے آئی رپورٹ · AI Report">{error ? <p className="text-red-600 font-bold">{error}</p> : <p>...</p>}</AppShell>;

  const s = d.scam_classifier_metrics, e = d.decision_engine_metrics, cm = s.confusion_matrix;
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;
  const card = (label: string, value: string) => (
    <div className="bg-white rounded-2xl shadow p-4 text-center"><p className="text-2xl font-bold text-emerald-700">{value}</p><p className="text-sm text-gray-500">{label}</p></div>
  );

  return (
    <AppShell title="اے آئی رپورٹ · AI Report">
      <p className="text-gray-600">Measured on {d.total_test_samples} test cases. The AI reads and explains; fixed rules decide.</p>

      <div className="grid grid-cols-2 gap-3">
        {card("Scam accuracy", pct(s.accuracy))}
        {card("False alarms", pct(s.false_alarm_rate))}
        {card("Auto-approved", e.auto_approve_rate)}
        {card("Auto-rejected", `${e.auto_reject_rate}%`)}
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-2">
        <p className="font-bold">Cost of being wrong — threshold sweep</p>
        <CostChart data={d.threshold_sweep_curve} best={e.optimal_p_wrong_threshold} />
        <p className="text-sm">Lowest cost <b>{e.min_expected_cost_per_case}</b> at threshold <b>{e.optimal_p_wrong_threshold}</b> (red circle). A wrong approval costs 10×, a human review 1×, asking for proof 0.4×.</p>
      </div>

      <div className="bg-white rounded-3xl shadow p-5">
        <p className="font-bold mb-2">Scam checker — confusion matrix</p>
        <div className="grid grid-cols-2 gap-2 text-center">
          <div className="bg-emerald-100 rounded-xl p-3"><b className="text-2xl">{cm.true_scam}</b><p className="text-sm">Scam caught</p></div>
          <div className="bg-red-100 rounded-xl p-3"><b className="text-2xl">{cm.missed_scam}</b><p className="text-sm">Scam missed</p></div>
          <div className="bg-amber-100 rounded-xl p-3"><b className="text-2xl">{cm.false_scam_alarm}</b><p className="text-sm">False alarm</p></div>
          <div className="bg-emerald-100 rounded-xl p-3"><b className="text-2xl">{cm.true_legit}</b><p className="text-sm">Legit passed</p></div>
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-2">
        <p className="font-bold">System guarantees</p>
        {d.system_guarantees.map((g) => (
          <p key={g.guarantee}>{g.verified ? "✅" : "❌"} <b>{g.guarantee}</b> — <span className="text-gray-600">{g.detail}</span></p>
        ))}
      </div>
    </AppShell>
  );
}