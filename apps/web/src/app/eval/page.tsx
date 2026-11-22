"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type EvalSummary } from "@/lib/api";

function CostChart({ data, best }: { data: EvalSummary["threshold_sweep_curve"]; best: number }) {
  const W = 620, H = 280, P = 45;
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
        {/* Grid lines */}
        <line x1={P} y1={H - P} x2={W - P} y2={H - P} stroke="#E2DDD3" strokeWidth={1.5} />
        <line x1={P} y1={P} x2={P} y2={H - P} stroke="#E2DDD3" strokeWidth={1.5} />

        {/* Sweep curve */}
        <polyline points={line} fill="none" stroke="#0B4F43" strokeWidth={3.5} strokeLinecap="round" />

        {/* Data points */}
        {data.map((d) => (
          <circle
            key={d.threshold}
            cx={sx(d.threshold)}
            cy={sy(d.expected_cost_per_case)}
            r={4.5}
            fill="#0B4F43"
          />
        ))}

        {/* Optimal Minimum Point Highlight (Red / Amber Ring) */}
        {bestPt && (
          <g>
            <circle
              cx={sx(bestPt.threshold)}
              cy={sy(bestPt.expected_cost_per_case)}
              r={11}
              fill="none"
              stroke="#E8A33D"
              strokeWidth={3.5}
              className="animate-pulse"
            />
            <circle
              cx={sx(bestPt.threshold)}
              cy={sy(bestPt.expected_cost_per_case)}
              r={4}
              fill="#E8A33D"
            />
            <text
              x={sx(bestPt.threshold)}
              y={sy(bestPt.expected_cost_per_case) - 14}
              textAnchor="middle"
              fontSize={11}
              fontWeight="bold"
              fill="#92400E"
            >
              Optimal ({bestPt.threshold})
            </text>
          </g>
        )}

        {/* Axis Labels */}
        <text x={W / 2} y={H - 10} textAnchor="middle" fontSize={11} fill="#5B6F6A" fontWeight="bold">
          Allowed Probability of Wrong Approval (P_wrong Threshold)
        </text>
        <text
          x={14}
          y={H / 2}
          fontSize={11}
          fill="#5B6F6A"
          fontWeight="bold"
          transform={`rotate(-90 14 ${H / 2})`}
          textAnchor="middle"
        >
          Expected Cost Per Case
        </text>

        {/* X Axis ticks */}
        {[x0, best, x1].map((t) => (
          <text key={t} x={sx(t)} y={H - P + 16} textAnchor="middle" fontSize={10} fill="#5B6F6A" fontFamily="monospace">
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
    api.getEvalSummary().then(setD).catch((e: ApiError) => setError(e.message_en ?? "Could not load eval summary"));
  }, []);

  if (!d) {
    return (
      <AppShell title="اے آئی کارکردگی رپورٹ · AI Evaluation">
        {error ? <p className="text-[#B3261E] font-bold p-4 bg-[#FEE2E2] rounded-2xl">{error}</p> : <p className="p-4">لوڈ ہو رہا ہے...</p>}
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
        <h2 className="text-xl font-bold text-[#0B4F43]">تجزیاتی رپورٹ اور لاگت تخمینہ · Decision Science & Sweep</h2>
        <p className="text-sm text-[#5B6F6A]">
          ماڈل {d.total_test_samples} تصدیق شدہ تاریخی ٹیسٹ کیسز پر جانچا گیا ہے۔ AI دستاویزات اور میسجز سمجھتا ہے، جبکہ مستحکم قواعد اور لاگت کا تجزیہ فیصلے کرتے ہیں۔
        </p>
      </Card>

      {/* Top 4 Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#0B4F43] font-mono">{pct(s.accuracy)}</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-1">Scam Accuracy</p>
        </Card>
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#C77700] font-mono">{pct(s.false_alarm_rate)}</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-1">False Alarms</p>
        </Card>
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#1F8A5B] font-mono">{e.auto_approve_rate}</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-1">Auto-Approved</p>
        </Card>
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#0B4F43] font-mono">{e.auto_reject_rate}%</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-1">Auto-Rejected (0%)</p>
        </Card>
      </div>

      {/* Cost of Being Wrong Sweep Curve */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-bold text-sm text-[#0B4F43]">
            غلط فیصلے کی لاگت کا سوئپ · Cost of Being Wrong (Threshold Sweep)
          </p>
          <span className="text-xs font-mono font-bold bg-[#FEF3C7] text-[#92400E] px-2.5 py-1 rounded-lg">
            Optimum: {e.optimal_p_wrong_threshold}
          </span>
        </div>

        <CostChart data={d.threshold_sweep_curve} best={e.optimal_p_wrong_threshold} />

        <div className="bg-[#F7F4EE] rounded-2xl p-3 border border-[#E2DDD3] text-xs text-[#17302B] space-y-1">
          <p className="font-bold">نظریہ و لاگت وزن (Asymmetric Cost Weights):</p>
          <p className="text-[#5B6F6A]">
            غلط منظوری (Wrong approval) = 10× لاگت، انسانی تفتیش (Human review) = 1× لاگت، اضافی ثبوت مانگنا = 0.4× لاگت۔
            سسٹم کم سے کم متوقع لاگت <b>{e.min_expected_cost_per_case}</b> پر تھریش ہولڈ <b>{e.optimal_p_wrong_threshold}</b> منتخب کرتا ہے۔
          </p>
        </div>
      </Card>

      {/* Scam Checker Confusion Matrix */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-[#0B4F43]">فراڈ ڈیٹیکشن میٹرکس · Scam Confusion Matrix</p>
        <div className="grid grid-cols-2 gap-3 text-center font-bold">
          <div className="bg-[#DDEFE9] border border-[#1F8A5B] rounded-2xl p-4 text-[#065F46]">
            <p className="text-3xl font-mono">{cm.true_scam}</p>
            <p className="text-xs mt-1">True Scam Caught (پکڑے گئے فراڈ)</p>
          </div>
          <div className="bg-[#FEE2E2] border border-[#B3261E] rounded-2xl p-4 text-[#7F1D1D]">
            <p className="text-3xl font-mono">{cm.missed_scam}</p>
            <p className="text-xs mt-1">Missed Scam (رہ جانے والے)</p>
          </div>
          <div className="bg-[#FEF3C7] border border-[#C77700] rounded-2xl p-4 text-[#92400E]">
            <p className="text-3xl font-mono">{cm.false_scam_alarm}</p>
            <p className="text-xs mt-1">False Alarm (غلط الارم)</p>
          </div>
          <div className="bg-[#DDEFE9] border border-[#1F8A5B] rounded-2xl p-4 text-[#065F46]">
            <p className="text-3xl font-mono">{cm.true_legit}</p>
            <p className="text-xs mt-1">True Legit Passed (اصلی میسجز)</p>
          </div>
        </div>
      </Card>

      {/* System Guarantees Checklist */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-[#0B4F43]">پلیٹ فارم کی حتمی سیکیورٹی ضمانتیں · Verified System Guarantees</p>
        <div className="space-y-2">
          {d.system_guarantees.map((g) => (
            <div
              key={g.guarantee}
              className="bg-[#F7F4EE] rounded-xl p-3 flex items-start gap-3 border border-[#E2DDD3] text-xs"
            >
              <span className="text-base shrink-0">{g.verified ? "✅" : "❌"}</span>
              <div>
                <p className="font-bold text-sm text-[#17302B]">{g.guarantee}</p>
                <p className="text-[#5B6F6A] mt-0.5">{g.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
