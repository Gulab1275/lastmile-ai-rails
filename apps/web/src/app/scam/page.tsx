"use client";

import { useState } from "react";
import { ShieldAlert, ShieldCheck, HelpCircle, Volume2, AlertOctagon, CheckCircle2, ArrowRight } from "lucide-react";
import AppShell from "@/components/appShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api, { type ApiError, type ScamCheckResponse, type ScamLabel } from "@/lib/api";
import { speak } from "@/lib/session";

const LOOK: Record<ScamLabel, { bg: string; border: string; ur: string; en: string; icon: React.ReactNode; statusBadge: "scam" | "approved" | "need_proof" }> = {
  scam: {
    bg: "bg-[#FEE2E2] text-[#7F1D1D]",
    border: "border-[#B3261E]",
    ur: "خبردار! یہ جعلی / فراڈ میسج ہے",
    en: "CONFIRMED SCAM — Do not reply or send money",
    icon: <ShieldAlert className="w-12 h-12 text-[#B3261E]" />,
    statusBadge: "scam",
  },
  legit: {
    bg: "bg-[#DDEFE9] text-[#065F46]",
    border: "border-[#1F8A5B]",
    ur: "یہ میسج محفوظ اور سرکاری لگتا ہے",
    en: "Official & Legitimate Communication",
    icon: <ShieldCheck className="w-12 h-12 text-[#1F8A5B]" />,
    statusBadge: "approved",
  },
  unsure: {
    bg: "bg-[#FEF3C7] text-[#92400E]",
    border: "border-[#C77700]",
    ur: "سسٹم کو مکمل یقین نہیں — انسانی جانچ تجویز ہے",
    en: "Uncertain / Suspicious — Human review recommended",
    icon: <HelpCircle className="w-12 h-12 text-[#C77700]" />,
    statusBadge: "need_proof",
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

// Highlight common risky scam triggers in Pakistan relief context
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
          className="bg-[#FEE2E2] text-[#991B1B] border border-[#F87171] px-1 py-0.5 rounded font-bold"
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
      setError(err.message_ur ?? err.message_en ?? "Could not check message with server");
    } finally {
      setLoading(false);
    }
  }

  const look = result ? LOOK[result.label] : null;

  return (
    <AppShell title="فراڈ چیکر · Relief Scam Guardian">
      <Card className="p-5 space-y-1.5">
        <h2 className="text-xl font-bold text-[#0B4F43]">مشکوک میسج کی فوری جانچ · Check Suspicious SMS</h2>
        <p className="text-sm text-[#5B6F6A]">
          کوئی بھی SMS یا WhatsApp میسج یہاں پیسٹ کریں۔ AI ماڈل فوری تجزیہ کر کے بتائے گا کہ کیا یہ دھوکہ یا فراڈ ہے۔
        </p>
      </Card>

      <Card className="p-5 space-y-3">
        <textarea
          className="w-full min-h-[130px] border-2 border-[#E2DDD3] rounded-2xl p-4 text-base bg-white text-[#17302B] focus:border-[#0F6B5A] focus:outline-none transition"
          placeholder="میسج یہاں پیسٹ کریں... / Paste SMS or WhatsApp message here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        {/* Quick Example Buttons */}
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="font-bold text-[#5B6F6A] self-center">آزمانے کے لیے نمونہ · Samples:</span>
          {EXAMPLES.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => { setText(ex.text); setResult(null); setError(""); setEscalated(false); }}
              type="button"
              className="px-3 py-1.5 rounded-xl bg-white border border-[#E2DDD3] text-[#0B4F43] font-bold hover:bg-[#DDEFE9] transition"
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
            className="w-full text-base"
          >
            {loading ? "ماڈل جانچ کر رہا ہے..." : "فراڈ چیک کریں · Analyze Message"}
          </Button>
        </div>
      </Card>

      {error && (
        <div className="bg-[#FEE2E2] border border-[#F87171] text-[#991B1B] rounded-2xl p-4 font-bold text-sm">
          {error}
        </div>
      )}

      {/* Analysis Result Card */}
      {result && look && (
        <div className={`rounded-3xl p-6 space-y-5 border-2 ${look.bg} ${look.border} shadow-lift animate-fade-up`}>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              {look.icon}
              <div>
                <p className="text-2xl font-bold leading-tight">{look.ur}</p>
                <p className="text-xs font-bold uppercase tracking-wider">{look.en}</p>
              </div>
            </div>
            <button
              onClick={() => speak(look.ur, "ur-PK")}
              type="button"
              className="min-h-[44px] min-w-[44px] rounded-2xl bg-white text-[#17302B] border border-[#E2DDD3] flex items-center justify-center shadow-sm hover:bg-slate-50 transition"
              aria-label="Listen verdict"
            >
              <Volume2 className="w-5 h-5" />
            </button>
          </div>

          {/* Highlighted text card */}
          <div className="bg-white rounded-2xl p-4 border border-[#E2DDD3] text-[#17302B] space-y-1.5 shadow-sm">
            <p className="text-xs font-bold text-[#5B6F6A] uppercase">تجزیہ شدہ میسج · Analyzed Text (Risky terms highlighted):</p>
            <p className="text-sm leading-relaxed">{highlightRiskyText(text)}</p>
          </div>

          {/* Critical Safety Guidance Banner */}
          {result.label === "scam" && (
            <div className="bg-[#991B1B] text-white rounded-2xl p-4 space-y-2 text-start shadow">
              <div className="flex items-center gap-2 font-bold text-base">
                <AlertOctagon className="w-6 h-6 shrink-0 text-[#FCD34D]" />
                <span>حفاظتی ہدایات · DO NOT CLICK OR PAY</span>
              </div>
              <ul className="list-disc ps-5 text-xs text-[#FEE2E2] space-y-1">
                <li>کسی بھی نامعلوم لنک پر کلک نہ کریں اور اپنا شناختی کارڈ یا OTP نہ دیں۔</li>
                <li>سرکاری احساس/بی آئی ایس پی امداد کی کوئی پیشگی فیس نہیں ہوتی۔ فیس مانگنے والا ہر میسج 100٪ دھوکہ ہے۔</li>
                <li>شکایت کے لیے پی ٹی اے ہیلپ لائن <b>8171</b> پر رابطہ کریں۔</li>
              </ul>
            </div>
          )}

          {/* Reasons List */}
          <div className="space-y-1.5 text-start">
            <div className="flex justify-between items-center text-xs font-bold">
              <span>ماڈل کے تجزیے کی وجوہات · Rationale</span>
              <span className="font-mono">یقین: {Math.round(result.confidence * 100)}%</span>
            </div>
            <ul className="list-disc ps-5 text-xs space-y-1 font-bold">
              {result.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>

          {/* Unsure Verdict: Route to Human Officer */}
          {result.label === "unsure" && (
            <div className="bg-white rounded-2xl p-4 border border-[#C77700] space-y-3 shadow-sm">
              <p className="text-sm font-bold text-[#92400E]">
                انسانی ریلیف افسر کو جانچ کے لیے بھیجیں · Forward to Human Review
              </p>
              <p className="text-xs text-[#5B6F6A]">
                اگر آپ کو یقین نہیں ہے، تو آپ یہ میسج ہمارے ریلیف آفیسر کو بھیج سکتے ہیں تاکہ وہ سرکاری ریکارڈ سے تصدیق کر سکے۔
              </p>
              {escalated ? (
                <div className="bg-[#DDEFE9] text-[#0B4F43] rounded-xl p-3 text-xs font-bold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#1F8A5B]" /> میسج ریلیف افسر کو بھیج دیا گیا ہے (Ticket #SCAM-894)
                </div>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEscalated(true)}
                >
                  افسر کو بھیجیں · Forward to Officer <ArrowRight className="w-4 h-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
