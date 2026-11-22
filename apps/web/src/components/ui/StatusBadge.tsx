"use client";

import React from "react";

export interface StatusBadgeProps {
  status: "approved" | "disbursed" | "need_proof" | "in_review" | "scam" | "legit" | "draft" | "active" | "revoked";
  labelUr?: string;
  labelEn?: string;
}

export function StatusBadge({ status, labelUr, labelEn }: StatusBadgeProps) {
  const configs = {
    approved: { bg: "bg-[#DDEFE9]", text: "text-[#065F46]", border: "border-[#1F8A5B]", dot: "bg-[#1F8A5B]", ur: "منظور", en: "Approved" },
    disbursed: { bg: "bg-[#DDEFE9]", text: "text-[#065F46]", border: "border-[#1F8A5B]", dot: "bg-[#1F8A5B]", ur: "رقم ادا شدہ", en: "Paid out" },
    need_proof: { bg: "bg-[#FEF3C7]", text: "text-[#92400E]", border: "border-[#C77700]", dot: "bg-[#C77700]", ur: "مزید ثبوت چاہیے", en: "Proof Needed" },
    in_review: { bg: "bg-[#EEF2FF]", text: "text-[#1E1B4B]", border: "border-[#4C5FD5]", dot: "bg-[#4C5FD5]", ur: "زیرِ جائزہ", en: "In Review" },
    scam: { bg: "bg-[#FEE2E2]", text: "text-[#7F1D1D]", border: "border-[#B3261E]", dot: "bg-[#B3261E]", ur: "فراڈ", en: "Scam" },
    legit: { bg: "bg-[#DDEFE9]", text: "text-[#065F46]", border: "border-[#1F8A5B]", dot: "bg-[#1F8A5B]", ur: "محفوظ", en: "Legit" },
    draft: { bg: "bg-slate-100", text: "text-[#5B6F6A]", border: "border-[#E2DDD3]", dot: "bg-[#5B6F6A]", ur: "مسودہ", en: "Draft" },
    active: { bg: "bg-[#DDEFE9]", text: "text-[#065F46]", border: "border-[#1F8A5B]", dot: "bg-[#1F8A5B]", ur: "فعال", en: "Active" },
    revoked: { bg: "bg-slate-100", text: "text-[#5B6F6A]", border: "border-[#E2DDD3]", dot: "bg-[#5B6F6A]", ur: "منسوخ", en: "Revoked" },
  };

  const cfg = configs[status] || configs.draft;

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
      <span>{labelUr || cfg.ur}</span>
      <span className="opacity-70 text-[10px]">· {labelEn || cfg.en}</span>
    </span>
  );
}
