"use client";

import { useState } from "react";

const REAL = [
  "Decision rules engine (fixed rules, no AI guessing)",
  "Confidence and cost thresholds",
  "Consent gateway (withdrawn consent = HTTP 403)",
  "Tamper-proof hash-chained audit log",
  "Scam classifier and document blur / tamper check",
  "Urdu voice and form extraction",
];
const SIMULATED = [
  "NADRA identity service (mock registry)",
  "Raast payment rail (mock payouts)",
  "Citizen complaints portal (mock)",
  "All people, CNICs and phone numbers are fake",
];

export default function PrototypeBanner() {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-amber-400 text-amber-950 text-sm">
      <button onClick={() => setOpen(!open)} className="w-full px-3 py-1 font-bold text-center" aria-expanded={open}>
        ⚠ PROTOTYPE ONLY — not an official service · نمونہ، سرکاری سروس نہیں · What is real vs simulated? {open ? "▲" : "▼"}
      </button>
      {open && (
        <div className="bg-white text-gray-800 p-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="font-bold text-emerald-700">✅ REAL · اصلی</p>
            <ul className="list-disc ps-5">{REAL.map((r) => <li key={r}>{r}</li>)}</ul>
          </div>
          <div>
            <p className="font-bold text-red-700">🧪 SIMULATED · نقلی</p>
            <ul className="list-disc ps-5">{SIMULATED.map((r) => <li key={r}>{r}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  );
}