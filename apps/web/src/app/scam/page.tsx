"use client";

import { useState } from "react";
import { ShieldAlert, ShieldCheck, HelpCircle, Volume2 } from "lucide-react";
import AppShell from "@/components/appShell";
import api, { type ApiError, type ScamCheckResponse, type ScamLabel } from "@/lib/api";
import { speak } from "@/lib/session";

const LOOK: Record<ScamLabel, { bg: string; ur: string; en: string; icon: React.ReactNode }> = {
  scam: { bg: "bg-red-100 text-red-800", ur: "خبردار! یہ فراڈ ہے", en: "SCAM — do not reply or click", icon: <ShieldAlert className="w-12 h-12" /> },
  legit: { bg: "bg-emerald-100 text-emerald-800", ur: "یہ میسج محفوظ لگتا ہے", en: "Looks legitimate", icon: <ShieldCheck className="w-12 h-12" /> },
  unsure: { bg: "bg-amber-100 text-amber-800", ur: "یقین نہیں — احتیاط کریں", en: "Not sure — be careful", icon: <HelpCircle className="w-12 h-12" /> },
};

const EXAMPLE =
  "مبارک ہو! آپ کا انعام نکلا ہے۔ فوری طور پر اپنا CNIC اور OTP اس لنک پر بھیجیں http://bit.ly/relief-pk";

export default function ScamPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ScamCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function check() {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const r = await api.checkScamSms(text);
      setResult(r);
      speak(LOOK[r.label].ur, "ur-PK");
    } catch (e) {
      const err = e as ApiError;
      setError(err.message_ur ?? err.message_en ?? "Error");
    } finally {
      setLoading(false);
    }
  }

  const look = result ? LOOK[result.label] : null;

  return (
    <AppShell title="فراڈ چیکر · Scam Checker">
      <p className="text-gray-600">
        مشکوک SMS یا WhatsApp میسج یہاں پیسٹ کریں۔ Paste a suspicious message below.
      </p>

      <textarea
        className="w-full h-40 border-2 rounded-2xl p-4 text-lg bg-white"
        placeholder="میسج یہاں پیسٹ کریں / Paste message here"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={check}
          disabled={loading || !text.trim()}
          className="h-14 rounded-2xl bg-emerald-600 text-white text-lg font-bold disabled:opacity-50"
        >
          {loading ? "..." : "چیک کریں · Check"}
        </button>
        <button
          onClick={() => setText(EXAMPLE)}
          className="h-14 rounded-2xl bg-emerald-100 text-emerald-800 text-lg font-bold"
        >
          مثال · Example
        </button>
      </div>

      {error && <p className="bg-red-100 text-red-700 rounded-2xl p-3 font-bold">{error}</p>}

      {result && look && (
        <div className={`rounded-3xl p-6 space-y-3 ${look.bg}`}>
          <div className="flex items-center gap-4">
            {look.icon}
            <div className="flex-1">
              <p className="text-2xl font-bold">{look.ur}</p>
              <p>{look.en}</p>
            </div>
            <button
              onClick={() => speak(look.ur, "ur-PK")}
              className="h-12 w-12 rounded-2xl bg-white/60 flex items-center justify-center"
              aria-label="Play audio"
            >
              <Volume2 className="w-6 h-6" />
            </button>
          </div>
          <p className="font-bold">Confidence: {Math.round(result.confidence * 100)}%</p>
          <ul className="list-disc ps-6 space-y-1">
            {result.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </AppShell>
  );
}