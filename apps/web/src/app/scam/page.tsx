"use client";

import { useState } from "react";
import { ShieldAlert, ShieldCheck, HelpCircle, Volume2, AlertOctagon, CheckCircle2, ArrowRight } from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import api, { type ApiError, type ScamCheckResponse, type ScamLabel } from "@/lib/api";
import { speak } from "@/lib/session";

const LOOK: Record<ScamLabel, { bg: string; border: string; ur: string; en: string; icon: React.ReactNode }> = {
  scam: {
    bg: "bg-rose-50 text-rose-950",
    border: "border-rose-300",
    ur: "خبردار! یہ جعلی / فراڈ میسج ہے",
    en: "CONFIRMED SCAM — Do not reply or send money",
    icon: <ShieldAlert className="w-10 h-10 text-rose-600 shrink-0" />,
  },
  legit: {
    bg: "bg-emerald-50 text-emerald-950",
    border: "border-emerald-300",
    ur: "یہ میسج محفوظ اور سرکاری لگتا ہے",
    en: "Official & Legitimate Communication",
    icon: <ShieldCheck className="w-10 h-10 text-emerald-600 shrink-0" />,
  },
  unsure: {
    bg: "bg-amber-50 text-amber-950",
    border: "border-amber-300",
    ur: "سسٹم کو مکمل یقین نہیں — انسانی جانچ تجویز ہے",
    en: "Uncertain / Suspicious — Human review recommended",
    icon: <HelpCircle className="w-10 h-10 text-amber-600 shrink-0" />,
  },
};

const EXAMPLES = [
  {
    label: "BISP Scam (فیس کا مطالبہ)",
    text: "BISP Mubarak! Apko 25,000 rupaye milay hain. 1500 fee bhaijain aur apna OTP is link per den http://bit.ly/bisp-cash",
  },
  {
    label: "Official BISP (سرکاری میسج 8171)",
    text: "Ap BISP Kafaalat k lye ahal hen. Apni qist 10,500 qareebi BISP markaz se biometric tasdeeq k zarye wasool karen. 8171",
  },
];

const RISKY_KEYWORDS = [
  "fee", "فیس", "otp", "pin", "bit.ly", "http", "25,000", "50,000", "انعام", "مبارک",
  "bhaijain", "bhaijo", "payment", "link", "claim", "urgent", "فوری",
];

function highlightRiskyText(text: string) {
  const words = text.split(/(\s+)/);
  return words.map((w, idx) => {
    const clean = w.toLowerCase().replace(/[^\w\u0600-\u06FF]/g, "");
    const isRisky = RISKY_KEYWORDS.some((k) => clean.includes(k) || w.startsWith("http"));
    if (isRisky) {
      return (
        <span
          key={idx}
          className="bg-rose-100 text-rose-800 border border-rose-300 px-1 py-0.5 rounded font-bold"
        >
          {w}
        </span>
      );
    }
    return <span key={idx}>{w}</span>;
  });
}

export default function ScamPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ScamCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [escalated, setEscalated] = useState(false);

  async function check() {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setEscalated(false);
    try {
      const r = await api.checkScamSms(text);
      setResult(r);
      speak(LOOK[r.label].ur, "ur-PK");
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Could not check message");
    } finally {
      setLoading(false);
    }
  }

  const look = result ? LOOK[result.label] : null;

  return (
    <AppShell title="فراڈ چیکر · Relief Scam Guardian">
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold font-heading text-slate-900">مشکوک میسج کی فوری جانچ · Check Suspicious SMS</h2>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          کوئی بھی SMS یا WhatsApp میسج یہاں پیسٹ کریں۔ AI ماڈل فوری تجزیہ کر کے بتائے گا کہ کیا یہ دھوکہ یا فراڈ ہے۔
        </p>
      </Card>

      <Card className="p-5 space-y-3.5">
        <textarea
          className="w-full min-h-[120px] border border-slate-300 rounded-xl p-3.5 text-sm bg-white text-slate-900 focus:border-[#0B4F43] focus:ring-1 focus:ring-[#0B4F43] focus:outline-none"
          placeholder="میسج یہاں پیسٹ کریں... / Paste SMS or WhatsApp message here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        {/* Quick Samples */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-slate-500">آزمانے کے لیے نمونہ:</span>
          {EXAMPLES.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => { setText(ex.text); setResult(null); setError(""); setEscalated(false); }}
              type="button"
              className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 font-medium transition"
            >
              {ex.label}
            </button>
          ))}
        </div>

        <div className="pt-1">
          <Button
            variant="primary"
            onClick={check}
            disabled={loading || !text.trim()}
            className="w-full"
          >
            {loading ? "ماڈل جانچ کر رہا ہے..." : "فراڈ چیک کریں · Analyze Message"}
          </Button>
        </div>
      </Card>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-3.5 font-medium text-xs">
          {error}
        </div>
      )}

      {/* Result Card */}
      {result && look && (
        <div className={`rounded-2xl p-5 sm:p-6 space-y-4 border ${look.bg} ${look.border} shadow-sm`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              {look.icon}
              <div className="space-y-0.5">
                <p className="text-xl font-bold font-heading leading-tight">{look.ur}</p>
                <p className="text-xs uppercase tracking-wider font-semibold opacity-80">{look.en}</p>
              </div>
            </div>
            <button
              onClick={() => speak(look.ur, "ur-PK")}
              type="button"
              className="p-2 rounded-lg bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 text-xs flex items-center gap-1 shadow-sm shrink-0"
              aria-label="Listen verdict"
            >
              <Volume2 className="w-4 h-4" /> سنیں
            </button>
          </div>

          {/* Highlighted text */}
          <div className="bg-white rounded-xl p-4 border border-slate-200 text-slate-900 space-y-1 shadow-sm">
            <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">تجزیہ شدہ عبارت · Analyzed Text:</p>
            <p className="text-xs sm:text-sm leading-relaxed">{highlightRiskyText(text)}</p>
          </div>

          {/* Guidance Banner */}
          {result.label === "scam" && (
            <div className="bg-rose-700 text-white rounded-xl p-4 space-y-2 text-xs shadow-sm">
              <div className="flex items-center gap-2 font-bold text-sm">
                <AlertOctagon className="w-5 h-5 text-amber-300 shrink-0" />
                <span>حفاظتی ہدایات · DO NOT CLICK OR PAY</span>
              </div>
              <ul className="list-disc ps-4 space-y-1 text-rose-100">
                <li>کسی بھی نامعلوم لنک پر کلک نہ کریں اور اپنا شناختی کارڈ یا OTP نہ دیں۔</li>
                <li>سرکاری امداد کی کوئی پیشگی فیس نہیں ہوتی۔ فیس مانگنے والا ہر میسج 100٪ دھوکہ ہے۔</li>
                <li>شکایت کے لیے پی ٹی اے ہیلپ لائن <b>8171</b> پر رابطہ کریں۔</li>
              </ul>
            </div>
          )}

          {/* Rationale */}
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between items-center font-bold">
              <span>ماڈل کے تجزیے کی وجوہات · Rationale:</span>
              <span className="font-mono">یقین: {Math.round(result.confidence * 100)}%</span>
            </div>
            <ul className="list-disc ps-4 space-y-1 font-medium">
              {result.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>

          {/* Escalation Button for Unsure */}
          {result.label === "unsure" && (
            <div className="bg-white rounded-xl p-4 border border-amber-300 space-y-2.5">
              <p className="text-xs sm:text-sm font-bold text-amber-950">
                انسانی ریلیف افسر کو جانچ کے لیے بھیجیں · Forward to Human Review
              </p>
              <p className="text-xs text-slate-600">
                اگر آپ کو یقین نہیں ہے، تو آپ یہ میسج ہمارے ریلیف آفیسر کو بھیج سکتے ہیں تاکہ وہ سرکاری ریکارڈ سے تصدیق کر سکے۔
              </p>
              {escalated ? (
                <div className="bg-emerald-50 text-emerald-800 rounded-lg p-2.5 text-xs font-semibold flex items-center gap-2 border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> میسج ریلیف افسر کو بھیج دیا گیا ہے (Ticket #SCAM-894)
                </div>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEscalated(true)}
                >
                  افسر کو بھیجیں · Forward to Officer <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
