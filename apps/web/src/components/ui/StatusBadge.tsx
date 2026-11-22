"use client";

import React from "react";

export interface StatusBadgeProps {
  status: "approved" | "disbursed" | "need_proof" | "in_review" | "scam" | "legit" | "draft" | "active" | "revoked";
  labelUr?: string;
  labelEn?: string;
}

export function StatusBadge({ status, labelUr, labelEn }: StatusBadgeProps) {
  const configs = {
    approved: { bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-300", dot: "bg-emerald-600", ur: "منظور", en: "Approved" },
    disbursed: { bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-300", dot: "bg-emerald-600", ur: "رقم ادا شدہ", en: "Disbursed" },
    need_proof: { bg: "bg-amber-50", text: "text-amber-900", border: "border-amber-300", dot: "bg-amber-600", ur: "مزید ثبوت درکار", en: "Proof Needed" },
    in_review: { bg: "bg-indigo-50", text: "text-indigo-900", border: "border-indigo-300", dot: "bg-indigo-600", ur: "زیرِ جائزہ", en: "In Review" },
    scam: { bg: "bg-rose-50", text: "text-rose-900", border: "border-rose-300", dot: "bg-rose-600", ur: "فراڈ میسج", en: "Scam" },
    legit: { bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-300", dot: "bg-emerald-600", ur: "محفوظ و اصلی", en: "Legit" },
    draft: { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-300", dot: "bg-slate-500", ur: "مسودہ", en: "Draft" },
    active: { bg: "bg-emerald-50", text: "text-emerald-800", border: "border-emerald-300", dot: "bg-emerald-600", ur: "فعال", en: "Active" },
    revoked: { bg: "bg-slate-100", text: "text-slate-600", border: "border-slate-300", dot: "bg-slate-400", ur: "منسوخ", en: "Revoked" },
  };

  const cfg = configs[status] || configs.draft;

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border} leading-tight`}>
      <span className={`w-2 h-2 rounded-full ${cfg.dot} shrink-0`} />
      <span>{labelUr || cfg.ur}</span>
      {labelEn && <span className="text-[11px] opacity-75 font-normal">({labelEn})</span>}
    </span>
  );
}
