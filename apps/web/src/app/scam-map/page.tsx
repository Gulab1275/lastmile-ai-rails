"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type Hotspot, type ScamMap } from "@/lib/api";

const COLOR: Record<string, string> = { CRITICAL: "#B3261E", HIGH: "#E8A33D", MODERATE: "#C77700" };
const pretty = (s: string) => s.replace(/_/g, " ");
const shortName = (d: string) => d.split(" (")[0];

function KarachiMap({ spots, rank }: { spots: Hotspot[]; rank: Map<string, number> }) {
  const W = 540, H = 340, P = 45;
  const lats = spots.map((s) => s.latitude);
  const lngs = spots.map((s) => s.longitude);
  const [la0, la1, lo0, lo1] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)];
  const x = (lng: number) => P + ((lng - lo0) / (lo1 - lo0 || 1)) * (W - 2 * P);
  const y = (lat: number) => H - P - ((lat - la0) / (la1 - la0 || 1)) * (H - 2 * P);

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full min-w-[500px] bg-[#E0F2FE]/40 rounded-2xl border border-[#BAE6FD]"
        style={{ direction: "ltr" }}
        role="img"
        aria-label="Karachi relief scam hotspots distribution map"
      >
        {/* Arabian Sea coastline outline aesthetic */}
        <path
          d={`M 0 ${H - 20} Q ${W * 0.3} ${H - 80} ${W * 0.7} ${H - 30} T ${W} ${H - 60}`}
          fill="none"
          stroke="#93C5FD"
          strokeWidth={2}
          strokeDasharray="4 4"
        />
        <text x={20} y={H - 15} fontSize={10} fill="#0369A1" fontWeight="bold">
          Arabian Sea Coastline (بحرِ عرب)
        </text>

        {spots.map((s) => (
          <g key={s.district}>
            {/* Pulsing Threat Radius */}
            <circle
              cx={x(s.longitude)}
              cy={y(s.latitude)}
              r={14 + s.threat_intensity * 18}
              fill={COLOR[s.threat_level]}
              fillOpacity={0.25}
            />
            {/* Center Pin Circle */}
            <circle
              cx={x(s.longitude)}
              cy={y(s.latitude)}
              r={13}
              fill={COLOR[s.threat_level]}
              stroke="#FFFFFF"
              strokeWidth={2}
            />
            {/* Rank Number */}
            <text
              x={x(s.longitude)}
              y={y(s.latitude) + 4.5}
              textAnchor="middle"
              fontSize={12}
              fontWeight="bold"
              fill="#FFFFFF"
            >
              {rank.get(s.district)}
            </text>
            {/* District Label */}
            <text
              x={x(s.longitude)}
              y={y(s.latitude) + 32}
              textAnchor="middle"
              fontSize={11}
              fontWeight="bold"
              fill="#17302B"
            >
              {shortName(s.district)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function ScamMapPage() {
  const [d, setD] = useState<ScamMap | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getScamMap().then(setD).catch((e: ApiError) => setError(e.message_en ?? "Could not load scam map"));
  }, []);

  if (!d) {
    return (
      <AppShell title="فراڈ نقشہ · Scam Map">
        {error ? <p className="text-[#B3261E] font-bold p-4 bg-[#FEE2E2] rounded-2xl">{error}</p> : <p className="p-4">لوڈ ہو رہا ہے...</p>}
      </AppShell>
    );
  }

  const ranked = [...d.hotspots].sort((a, b) => b.threat_intensity - a.threat_intensity);
  const rank = new Map(ranked.map((h, i) => [h.district, i + 1]));
  const karachi = d.hotspots.filter((h) => h.latitude < 25.1 && h.longitude < 67.5);
  const catMax = Math.max(...Object.values(d.category_distribution), 1);
  const dayMax = Math.max(...d.temporal_trends.map((t) => t.blocked_scams), 1);

  return (
    <AppShell title="فراڈ نقشہ · Scam Heatmap">
      {/* Citizen Advisory Banner */}
      <div className="bg-[#FEE2E2] border-2 border-[#B3261E] rounded-3xl p-5 space-y-1.5 shadow-soft">
        <p className="text-xl font-bold text-[#7F1D1D]">{d.summary.citizen_protection_advice_ur}</p>
        <p className="text-sm text-[#991B1B]">{d.summary.citizen_protection_advice_en}</p>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#0B4F43] font-mono">{d.total_active_clusters}</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-0.5">Active Hotspots</p>
        </Card>
        <Card className="p-4">
          <p className="text-3xl font-bold text-[#0B4F43] font-mono">{d.total_analyzed_threats}</p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-0.5">Threats Analyzed</p>
        </Card>
        <Card className="p-4">
          <p className="text-base font-bold text-[#B3261E] leading-tight truncate">
            {shortName(d.summary.highest_risk_district)}
          </p>
          <p className="text-xs text-[#5B6F6A] font-bold mt-0.5">Highest Risk Zone</p>
        </Card>
      </div>

      {/* Interactive Karachi Hotspot Map */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-bold text-sm text-[#0B4F43]">
            کراچی فراڈ کلسٹرز · Karachi Threat Map (Numbered by Risk Rank)
          </p>
          <div className="flex gap-3 text-xs font-bold">
            <span className="flex items-center gap-1 text-[#B3261E]">● Critical</span>
            <span className="flex items-center gap-1 text-[#E8A33D]">● High</span>
            <span className="flex items-center gap-1 text-[#C77700]">● Moderate</span>
          </div>
        </div>

        <KarachiMap spots={karachi} rank={rank} />
      </Card>

      {/* Highest Risk Areas List */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-[#0B4F43]">تمام اضلاع بترتیب خطرہ · All Areas by Threat Intensity</p>
        <div className="space-y-3">
          {ranked.map((h, i) => (
            <div key={h.district} className="space-y-1 text-xs">
              <div className="flex justify-between font-bold text-sm">
                <span className="text-[#17302B]">{i + 1}. {h.district}</span>
                <span style={{ color: COLOR[h.threat_level] }}>{h.threat_level}</span>
              </div>
              <div className="h-3 bg-[#E2DDD3] rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-500"
                  style={{ width: `${h.threat_intensity * 100}%`, backgroundColor: COLOR[h.threat_level] }}
                />
              </div>
              <p className="text-[11px] text-[#5B6F6A]">
                {h.incident_count} reports recorded · Primary threat: <b>{pretty(h.primary_scam_type)}</b>
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Threat Category Distribution */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-[#0B4F43]">فراڈ کی اقسام · Scam Category Breakdown</p>
        <div className="space-y-2">
          {Object.entries(d.category_distribution).map(([k, n]) => (
            <div key={k} className="flex items-center gap-3 text-xs">
              <span className="w-40 font-bold capitalize text-[#17302B] truncate">{pretty(k)}</span>
              <div className="flex-1 h-3 bg-[#E2DDD3] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#0B4F43] transition-all duration-500"
                  style={{ width: `${(n / catMax) * 100}%` }}
                />
              </div>
              <span className="w-8 text-end font-mono font-bold">{n}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Top Keywords Chips */}
      <Card className="p-5 space-y-2.5">
        <p className="font-bold text-sm text-[#0B4F43]">دھوکے بازوں کے اہم الفاظ · Frequent Scam Keywords</p>
        <div className="flex flex-wrap gap-2">
          {d.top_keywords.map((k) => (
            <span
              key={k.keyword_en}
              className="px-3 py-1 rounded-full bg-[#FEE2E2] text-[#7F1D1D] border border-[#F87171] font-bold text-xs"
            >
              {k.keyword_ur} · {k.keyword_en} ({k.frequency})
            </span>
          ))}
        </div>
      </Card>

      {/* Temporal Trend Chart */}
      <Card className="p-5 space-y-3">
        <p className="font-bold text-sm text-[#0B4F43]">
          پچھلے {d.temporal_trends.length} دنوں میں روکے گئے حملے · Blocked Threat Trend
        </p>
        <div className="flex items-end gap-2.5 h-36 pt-4" style={{ direction: "ltr" }}>
          {d.temporal_trends.map((t) => (
            <div key={t.date} className="flex-1 flex flex-col items-center justify-end h-full">
              <span className="text-[11px] font-mono font-bold text-[#0B4F43] mb-1">{t.blocked_scams}</span>
              <div
                className="w-full bg-[#1F8A5B] rounded-t-lg transition-all duration-500 hover:bg-[#0B4F43]"
                style={{ height: `${(t.blocked_scams / dayMax) * 100}%` }}
              />
              <span className="text-[9px] text-[#5B6F6A] font-mono mt-1">{t.date.slice(5)}</span>
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
