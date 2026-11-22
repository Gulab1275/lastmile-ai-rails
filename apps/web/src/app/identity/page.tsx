"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, WifiOff, Fingerprint, ShieldAlert } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type NadraResult } from "@/lib/api";

const PRESETS = [
  { label: "Spelling variant (Muhammad vs Mohammad)", cnic: "42101-7654321-2", name: "Muhammad Tariq" },
  { label: "Typo / Phonetic slip (Mohamad Tarik)", cnic: "42101-7654321-2", name: "Mohamad Tarik" },
  { label: "Urdu text (پروین بی بی)", cnic: "42101-1234567-1", name: "پروین بی بی" },
  { label: "Wrong name (Mismatch)", cnic: "42101-1234567-1", name: "Ahmed Raza" },
  { label: "CNIC not found (Incomplete)", cnic: "42101-0000000-0", name: "Ali Khan" },
  { label: "Deceased citizen test", cnic: "42301-5555555-5", name: "Deceased Record Test" },
];

function verdict(r: NadraResult) {
  if (r.deceased)
    return {
      tone: "bg-[#FEE2E2] text-[#7F1D1D] border-2 border-[#B3261E]",
      icon: <ShieldAlert className="w-10 h-10 text-[#B3261E]" />,
      ur: "یہ ریکارڈ فوت شدہ شہری کا ہے",
      en: "Record flagged as deceased person. Forwarded to officer for fraud prevention.",
    };
  if (r.status === "RECORD_NOT_FOUND")
    return {
      tone: "bg-[#FEF3C7] text-[#92400E] border-2 border-[#C77700]",
      icon: <AlertTriangle className="w-10 h-10 text-[#C77700]" />,
      ur: "نادرا ریکارڈ میں یہ شناختی کارڈ نہیں ملا",
      en: "No record found for this CNIC. Requires physical verification or officer review.",
    };
  if (r.matched && r.match_score >= 0.9)
    return {
      tone: "bg-[#DDEFE9] text-[#065F46] border-2 border-[#1F8A5B]",
      icon: <CheckCircle2 className="w-10 h-10 text-[#1F8A5B]" />,
      ur: "مکمل تصدیق شدہ — ایک ہی شخص ہے",
      en: "Biometric and phonetic match confirmed. Differences are minor spelling variants.",
    };
  if (r.matched)
    return {
      tone: "bg-[#FEF3C7] text-[#92400E] border-2 border-[#C77700]",
      icon: <AlertTriangle className="w-10 h-10 text-[#C77700]" />,
      ur: "غالباً وہی شخص ہے — افسر تصدیق کرے گا",
      en: "Probable phonetic match. Officer confirmation required before disbursement.",
    };
  return {
    tone: "bg-[#EEF2FF] text-[#1E1B4B] border-2 border-[#4C5FD5]",
    icon: <XCircle className="w-10 h-10 text-[#4C5FD5]" />,
    ur: "نام مماثلت نہیں رکھتا — افسر جائزہ لے گا",
    en: "Name mismatch. Sent to human review. The citizen is NEVER auto-rejected.",
  };
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
    <AppShell title="شناخت جانچ · NADRA Identity Verification">
      <div className="bg-white rounded-3xl p-5 border border-[#E2DDD3] shadow-sm space-y-1">
        <div className="flex items-center gap-2 text-[#0B4F43]">
          <Fingerprint className="w-6 h-6" />
          <h2 className="text-xl font-bold">نادرا فزی شناخت جانچ · NADRA Verification Rail</h2>
        </div>
        <p className="text-xs text-[#5B6F6A]">
          پاکستانی ناموں کے ہجے مختلف ہو سکتے ہیں (مثلاً Muhammad اور Mohammad)۔ ہمارا ماڈل حروف کے بجائے مماثلت اسکورنگ (Phonetic Transliteration) سے شناخت جانچتا ہے۔
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="space-y-1">
        <p className="text-xs font-bold text-[#5B6F6A]">جانچ کے نمونے · Quick Test Cases:</p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => { setCnic(p.cnic); setName(p.name); run(p.cnic, p.name); }}
              type="button"
              className="min-h-[38px] px-3 rounded-full bg-white border border-[#E2DDD3] text-[#0B4F43] hover:bg-[#DDEFE9] font-bold text-xs transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="bg-white rounded-3xl shadow p-5 space-y-3 border border-[#E2DDD3]">
        <input
          className="w-full min-h-[50px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A]"
          placeholder="شناختی کارڈ نمبر / CNIC (e.g. 42101-1234567-1)"
          inputMode="numeric"
          value={cnic}
          onChange={(e) => setCnic(e.target.value)}
        />
        <input
          className="w-full min-h-[50px] border-2 border-[#E2DDD3] rounded-2xl px-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A]"
          placeholder="فارم پر درج نام / Full name on the application"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* Chaos Mode Injection */}
        <div className="flex items-center justify-between text-xs bg-[#F7F4EE] p-3 rounded-2xl border border-[#E2DDD3]">
          <span className="font-bold text-[#17302B]">کیوس موڈ جانچ · Inject Rail Chaos:</span>
          <select
            className="border-2 border-[#E2DDD3] rounded-xl min-h-[36px] px-2.5 bg-white text-xs font-bold"
            value={chaos}
            onChange={(e) => setChaos(e.target.value)}
          >
            <option value="none">عام حالت · Normal (none)</option>
            <option value="timeout">نیٹ ورک تاخیر · Timeout</option>
            <option value="500">سرور خرابی · Server 500 error</option>
            <option value="slow">سست رفتار · Slow (2s+)</option>
          </select>
        </div>

        <button
          onClick={() => run()}
          disabled={busy || !cnic || !name}
          type="button"
          className="w-full min-h-[50px] rounded-2xl bg-[#0B4F43] text-white text-base font-bold shadow hover:bg-[#093e34] transition disabled:opacity-40"
        >
          {busy ? "نادرا سے تصدیق ہو رہی ہے..." : "شناخت جانچیں · Run NADRA Verification"}
        </button>
      </div>

      {/* Down / Timeout Failure Card */}
      {down && (
        <div className="rounded-3xl p-5 bg-[#E0F2FE] border-2 border-[#38BDF8] text-[#075985] flex gap-4 items-start shadow animate-fade-up">
          <WifiOff className="w-10 h-10 shrink-0 text-[#0284C7]" />
          <div className="space-y-1">
            <p className="text-lg font-bold">نادرا سروس فی الحال دستیاب نہیں ہے · Service Resilience</p>
            <p className="text-xs">{down.message_en ?? "External rail timeout"}</p>
            <p className="text-xs font-bold text-[#0B4F43] pt-1">
              پالیسی کے مطابق شہری کو مسترد نہیں کیا گیا ہے۔ کیس قطار میں رہے گا اور نیٹ ورک بحال ہوتے ہی دوبارہ جانچا جائے گا۔
            </p>
          </div>
        </div>
      )}

      {/* Verification Result Card */}
      {res && v && (
        <div className={`rounded-3xl p-6 space-y-4 shadow-lift animate-fade-up ${v.tone}`}>
          <div className="flex items-center gap-3">
            {v.icon}
            <div>
              <p className="text-xl font-bold leading-tight">{v.ur}</p>
              <p className="text-xs uppercase tracking-wide font-bold">{v.en}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 bg-white/70 rounded-2xl p-3 text-center border border-current text-xs">
            <div>
              <p className="text-[#5B6F6A]">فارم پر درج شدہ نام:</p>
              <p className="font-bold text-[#17302B] text-sm">{name}</p>
            </div>
            <div>
              <p className="text-[#5B6F6A]">نادرا کا سرکاری ریکارڈ:</p>
              <p className="font-bold text-[#17302B] text-sm">{res.canonical_name}</p>
            </div>
          </div>

          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="font-bold">نام کا مماثلت اسکور · Match Score:</span>
              <span className="font-mono font-bold">{Math.round(res.match_score * 100)}%</span>
            </div>
            <div className="h-4 bg-white/80 rounded-full overflow-hidden relative border border-[#E2DDD3]">
              <div
                className={`h-full ${res.match_score >= 0.7 ? "bg-[#1F8A5B]" : "bg-[#C77700]"}`}
                style={{ width: `${res.match_score * 100}%` }}
              />
            </div>
            <p className="text-[10px] text-[#5B6F6A] pt-1">
              Status: <span className="font-mono font-bold">{res.status}</span> · Latency: {res.latency_ms} ms
            </p>
          </div>
        </div>
      )}
    </AppShell>
  );
}
