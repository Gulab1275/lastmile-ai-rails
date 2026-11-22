"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import api, { type ApiError, type EvalSummary } from "@/lib/api";

function CostChart({ data, best }: { data: EvalSummary["threshold_sweep_curve"]; best: number }) {
  const W = 620, H = 260, P = 45;
  const xs = data.map((d) => d.threshold);
  const ys = data.map((d) => d.expected_cost_per_case);
  const [x0, x1, y1] = [Math.min(...xs), Math.max(...xs), Math.max(...ys) * 1.15 || 1];
  const sx = (x: number) => P + ((x - x0) / (x1 - x0 || 1)) * (W - 2 * P);
  const sy = (y: number) => H - P - (y / y1) * (H - 2 * P);
  const line = data.map((d) => `${sx(d.threshold)},${sy(d.expected_cost_per_case)}`).join(" ");
  const bestPt = data.find((d) => d.threshold === best);

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full min-w-[500px]"
        style={{ direction: "ltr" }}
        role="img"
        aria-label="Expected cost vs threshold sweep curve"
      >
        <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#CBD5E1" strokeWidth={1} />
        <line x1={P} y1={P} x2={P} y2={H - P} stroke="#CBD5E1" strokeWidth={1} />

        <polyline points={line} fill="none" stroke="#0B4F43" strokeWidth={3} strokeLinecap="round" />

        {data.map((d) => (
          <circle
            key={d.threshold}
            cx={sx(d.threshold)}
            cy={sy(d.expected_cost_per_case)}
            r={4}
            fill="#0B4F43"
          />
        ))}

        {bestPt && (
          <g>
            <circle
              cx={sx(bestPt.threshold)}
              cy={sy(bestPt.expected_cost_per_case)}
              r={10}
              fill="none"
              stroke="#D97706"
              strokeWidth={3}
            />
            <circle
              cx={sx(bestPt.threshold)}
              cy={sy(bestPt.expected_cost_per_case)}
              r={4}
              fill="#D97706"
            />
            <text
              x={sx(bestPt.threshold)}
              y={sy(bestPt.expected_cost_per_case) - 12}
              textAnchor="middle"
              fontSize={11}
              fontWeight="bold"
              fill="#92400E"
            >
              Optimal ({bestPt.threshold})
            </text>
          </g>
        )}

        <text x={W / 2} y={H - 10} textAnchor="middle" fontSize={11} fill="#64748B">
          Allowed Probability of Wrong Approval (Threshold)
        </text>
        <text
          x={14}
          y={H / 2}
          fontSize={11}
          fill="#64748B"
          transform={`rotate(-90 14 ${H / 2})`}
          textAnchor="middle"
        >
          Expected Cost Per Case
        </text>

        {[x0, best, x1].map((t) => (
          <text key={t} x={sx(t)} y={H - P + 16} textAnchor="middle" fontSize={10} fill="#64748B" fontFamily="monospace">
            {t}
          </text>
        ))}
      </svg>
    </div>
  );
}

export default function EvalPage() {
  const [d, setD] = useState<EvalSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getEvalSummary().then(setD).catch((e: ApiError) => setError(e.message_en ?? "Could not load"));
  }, []);

  if (!d) {
    return (
      <AppShell title="اے آئی رپورٹ · AI Report">
        {error ? <p className="text-rose-700 font-bold p-4 bg-rose-50 rounded-xl">{error}</p> : <p className="p-4 text-xs text-slate-500">لوڈ ہو رہا ہے...</p>}
      </AppShell>
    );
  }

  const s = d.scam_classifier_metrics;
  const e = d.decision_engine_metrics;
  const cm = s.confusion_matrix;
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

  return (
    <AppShell title="اے آئی کارکردگی رپورٹ · AI Evaluation">
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">تجزیاتی رپورٹ اور لاگت تخمینہ · Decision Science & Sweep</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          ماڈل {d.total_test_samples} تصدیق شدہ تاریخی ٹیسٹ کیسز پر جانچا گیا ہے۔ AI دستاویزات اور میسجز سمجھتا ہے، جبکہ مستحکم قواعد اور لاگت کا تجزیہ فیصلے کرتے ہیں۔
        </p>
      </Card>

      {/* 4 Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <Card className="p-4">
          <p className="text-2xl sm:text-3xl font-bold text-[#0B4F43] font-mono">{pct(s.accuracy)}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Scam Accuracy</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl sm:text-3xl font-bold text-amber-700 font-mono">{pct(s.false_alarm_rate)}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">False Alarms</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl sm:text-3xl font-bold text-emerald-700 font-mono">{e.auto_approve_rate}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Auto-Approved</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl sm:text-3xl font-bold text-[#0B4F43] font-mono">{e.auto_reject_rate}%</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Auto-Rejected (0%)</p>
        </Card>
      </div>

      {/* Sweep Curve */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-bold text-sm text-slate-900">
            غلط فیصلے کی لاگت کا تجزیہ · Cost of Being Wrong (Sweep Curve)
          </p>
          <span className="text-xs font-mono font-bold bg-amber-100 text-amber-900 px-2.5 py-0.5 rounded">
            Optimum: {e.optimal_p_wrong_threshold}
          </span>
        </div>

        <CostChart data={d.threshold_sweep_curve} best={e.optimal_p_wrong_threshold} />

        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs text-slate-700 space-y-1">
          <p className="font-bold text-slate-900">نظریہ و لاگت وزن (Asymmetric Cost Weights):</p>
          <p className="text-slate-600 leading-relaxed">
            غلط منظوری (Wrong approval) = 10× لاگت، انسانی تفتیش (Human review) = 1× لاگت، اضافی ثبوت مانگنا = 0.4× لاگت۔
            سسٹم کم سے کم متوقع لاگت <b>{e.min_expected_cost_per_case}</b> پر تھریش ہولڈ <b>{e.optimal_p_wrong_threshold}</b> منتخب کرتا ہے۔
          </p>
        </div>
      </Card>

      {/* Confusion Matrix */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-slate-900">فراڈ ڈیٹیکشن میٹرکس · Scam Confusion Matrix</p>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 text-emerald-950">
            <p className="text-2xl sm:text-3xl font-mono font-bold">{cm.true_scam}</p>
            <p className="text-xs mt-0.5 font-medium">True Scam Caught (پکڑے گئے)</p>
          </div>
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 text-rose-950">
            <p className="text-2xl sm:text-3xl font-mono font-bold">{cm.missed_scam}</p>
            <p className="text-xs mt-0.5 font-medium">Missed Scam (رہ جانے والے)</p>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-amber-950">
            <p className="text-2xl sm:text-3xl font-mono font-bold">{cm.false_scam_alarm}</p>
            <p className="text-xs mt-0.5 font-medium">False Alarm (غلط الارم)</p>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 text-emerald-950">
            <p className="text-2xl sm:text-3xl font-mono font-bold">{cm.true_legit}</p>
            <p className="text-xs mt-0.5 font-medium">True Legit (اصلی میسجز)</p>
          </div>
        </div>
      </Card>

      {/* System Guarantees */}
      <Card className="p-5 space-y-2.5">
        <p className="font-bold text-sm text-slate-900">پلیٹ فارم کی حتمی سیکیورٹی ضمانتیں · Verified System Guarantees</p>
        <div className="space-y-2">
          {d.system_guarantees.map((g) => (
            <div
              key={g.guarantee}
              className="bg-slate-50 rounded-xl p-3 flex items-start gap-2.5 border border-slate-200 text-xs"
            >
              <span className="text-sm shrink-0 mt-0.5">{g.verified ? "✅" : "❌"}</span>
              <div className="space-y-0.5">
                <p className="font-bold text-slate-900">{g.guarantee}</p>
                <p className="text-slate-500 leading-normal">{g.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
