"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type Hotspot, type ScamMap } from "@/lib/api";

const COLOR: Record<string, string> = { CRITICAL: "#dc2626", HIGH: "#f97316", MODERATE: "#eab308" };
const pretty = (s: string) => s.replace(/_/g, " ");
const shortName = (d: string) => d.split(" (")[0];

function KarachiMap({ spots, rank }: { spots: Hotspot[]; rank: Map<string, number> }) {
  const W = 520, H = 320, P = 40;
  const lats = spots.map((s) => s.latitude), lngs = spots.map((s) => s.longitude);
  const [la0, la1, lo0, lo1] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)];
  const x = (lng: number) => P + ((lng - lo0) / (lo1 - lo0 || 1)) * (W - 2 * P);
  const y = (lat: number) => H - P - ((lat - la0) / (la1 - la0 || 1)) * (H - 2 * P);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full bg-sky-50 rounded-2xl" style={{ direction: "ltr" }} role="img" aria-label="Karachi scam hotspots">
      {spots.map((s) => (
        <g key={s.district}>
          <circle cx={x(s.longitude)} cy={y(s.latitude)} r={14 + s.threat_intensity * 16} fill={COLOR[s.threat_level]} fillOpacity={0.35} />
          <circle cx={x(s.longitude)} cy={y(s.latitude)} r={13} fill={COLOR[s.threat_level]} />
          <text x={x(s.longitude)} y={y(s.latitude) + 5} textAnchor="middle" fontSize={14} fontWeight="bold" fill="#fff">{rank.get(s.district)}</text>
          <text x={x(s.longitude)} y={y(s.latitude) + 36} textAnchor="middle" fontSize={11} fill="#334155">{shortName(s.district)}</text>
        </g>
      ))}
    </svg>
  );
}

export default function ScamMapPage() {
  const [d, setD] = useState<ScamMap | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.getScamMap().then(setD).catch((e: ApiError) => setError(e.message_en ?? "Could not load")); }, []);

  if (!d) return <AppShell title="فراڈ نقشہ · Scam Map">{error ? <p className="text-red-600 font-bold">{error}</p> : <p>...</p>}</AppShell>;

  const ranked = [...d.hotspots].sort((a, b) => b.threat_intensity - a.threat_intensity);
  const rank = new Map(ranked.map((h, i) => [h.district, i + 1]));
  const karachi = d.hotspots.filter((h) => h.latitude < 25.1 && h.longitude < 67.5);
  const catMax = Math.max(...Object.values(d.category_distribution), 1);
  const dayMax = Math.max(...d.temporal_trends.map((t) => t.blocked_scams), 1);

  return (
    <AppShell title="فراڈ نقشہ · Scam Map">
      <div className="bg-red-50 border-2 border-red-200 rounded-3xl p-5 space-y-1">
        <p className="text-xl font-bold text-red-800">{d.summary.citizen_protection_advice_ur}</p>
        <p className="text-red-700">{d.summary.citizen_protection_advice_en}</p>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-white rounded-2xl shadow p-3"><p className="text-2xl font-bold text-emerald-700">{d.total_active_clusters}</p><p className="text-xs text-gray-500">Active areas</p></div>
        <div className="bg-white rounded-2xl shadow p-3"><p className="text-2xl font-bold text-emerald-700">{d.total_analyzed_threats}</p><p className="text-xs text-gray-500">Threats analysed</p></div>
        <div className="bg-white rounded-2xl shadow p-3"><p className="text-sm font-bold text-red-700 leading-tight">{shortName(d.summary.highest_risk_district)}</p><p className="text-xs text-gray-500">Highest risk</p></div>
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-3">
        <p className="font-bold">Karachi hotspots (number = risk rank)</p>
        <KarachiMap spots={karachi} rank={rank} />
        <div className="flex gap-4 text-sm"><span style={{ color: COLOR.CRITICAL }}>● Critical</span><span style={{ color: COLOR.HIGH }}>● High</span><span style={{ color: COLOR.MODERATE }}>● Moderate</span></div>
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-2">
        <p className="font-bold">All areas, highest risk first</p>
        {ranked.map((h, i) => (
          <div key={h.district} className="text-sm">
            <div className="flex justify-between"><span>{i + 1}. {h.district}</span><b style={{ color: COLOR[h.threat_level] }}>{h.threat_level}</b></div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden"><div className="h-full" style={{ width: `${h.threat_intensity * 100}%`, background: COLOR[h.threat_level] }} /></div>
            <p className="text-xs text-gray-500">{h.incident_count} reports · mostly {pretty(h.primary_scam_type)}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-3xl shadow p-5 space-y-2">
        <p className="font-bold">Scam types</p>
        {Object.entries(d.category_distribution).map(([k, n]) => (
          <div key={k} className="flex items-center gap-2 text-sm">
            <span className="w-40 capitalize">{pretty(k)}</span>
            <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden"><div className="h-full bg-emerald-600" style={{ width: `${(n / catMax) * 100}%` }} /></div>
            <b className="w-6 text-end">{n}</b>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-3xl shadow p-5">
        <p className="font-bold mb-2">Words scammers use</p>
        <div className="flex flex-wrap gap-2">
          {d.top_keywords.map((k) => <span key={k.keyword_en} className="px-3 py-1 rounded-full bg-red-100 text-red-800 font-bold">{k.keyword_ur} · {k.keyword_en} ({k.frequency})</span>)}
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow p-5">
        <p className="font-bold mb-2">Scams blocked, last {d.temporal_trends.length} days</p>
        <div className="flex items-end gap-2 h-32" style={{ direction: "ltr" }}>
          {d.temporal_trends.map((t) => (
            <div key={t.date} className="flex-1 flex flex-col items-center justify-end h-full">
              <span className="text-xs font-bold">{t.blocked_scams}</span>
              <div className="w-full bg-emerald-500 rounded-t" style={{ height: `${(t.blocked_scams / dayMax) * 100}%` }} />
              <span className="text-[10px] text-gray-500">{t.date.slice(5)}</span>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}