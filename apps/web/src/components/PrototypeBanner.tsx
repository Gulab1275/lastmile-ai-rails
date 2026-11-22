"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";

const REAL = [
  "Deterministic rules engine (versioned rules, no hallucinations)",
  "Weakest-link confidence & zero auto-reject invariant",
  "Consent gateway (revoked consent = instant HTTP 403)",
  "Tamper-proof cryptographic SHA-256 audit hash chain",
  "AI scam classifier with Roman Urdu fee disambiguation",
  "Document OCR blur gate and Urdu voice TTS/STT",
];
const SIMULATED = [
  "NADRA identity verification (sandbox mock registry)",
  "Raast fast payment rails (mock cryptographic payouts)",
  "All citizen profiles, CNICs and phone numbers are demo data",
];

export default function PrototypeBanner() {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-[#E8A33D] text-[#17302B] text-xs border-b border-[#C77700] z-50 relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-full min-h-[34px] px-3 py-1.5 font-bold text-center flex items-center justify-between gap-1.5 hover:bg-[#d9942e] transition"
        aria-expanded={open}
        type="button"
      >
        <div className="flex items-center gap-1.5 mx-auto sm:mx-0">
          <AlertTriangle className="w-4 h-4 shrink-0 text-[#17302B]" />
          <span>PROTOTYPE — not an official government service · پروٹوٹائپ (سرکاری سروس نہیں)</span>
          <span className="underline ml-1">تفصیل / What is real?</span>
          {open ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
        </div>
        <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono">
          <span className="bg-[#17302B]/15 px-2 py-0.5 rounded-full font-semibold">AWS EC2 Sovereign Rails</span>
          <span className="bg-[#17302B]/15 px-2 py-0.5 rounded-full font-semibold">SHA-256 Audit Intact</span>
        </div>
      </button>
      {open && (
        <div className="bg-white text-[#17302B] p-4 grid gap-4 sm:grid-cols-2 border-b border-[#E2DDD3] text-xs animate-fade-up">
          <div className="bg-[#DDEFE9] p-3 rounded-2xl border border-[#1F8A5B]/30 space-y-1">
            <p className="font-bold text-[#0B4F43]">✅ REAL & PRODUCTION READY · اصلی</p>
            <ul className="list-disc ps-5 space-y-1 text-[#065F46]">
              {REAL.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
          <div className="bg-[#FEF3C7] p-3 rounded-2xl border border-[#FCD34D] space-y-1">
            <p className="font-bold text-[#92400E]">🧪 SANDBOX / SIMULATED · نقلی نمونہ</p>
            <ul className="list-disc ps-5 space-y-1 text-[#78350F]">
              {SIMULATED.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
