"use client";

import React from "react";

interface BigToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  labelUr: string;
  labelEn: string;
  descUr?: string;
}

export function BigToggle({
  checked,
  onChange,
  disabled = false,
  labelUr,
  labelEn,
  descUr,
}: BigToggleProps) {
  return (
    <div
      onClick={() => !disabled && onChange(!checked)}
      className={`min-h-[58px] p-4 rounded-2xl border-2 flex items-center justify-between cursor-pointer transition select-none ${
        checked
          ? "bg-[#DDEFE9]/70 border-[#1F8A5B] text-[#065F46]"
          : "bg-white border-[#E2DDD3] text-[#5B6F6A] hover:bg-slate-50"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <div className="space-y-0.5">
        <p className="font-bold text-sm text-[#17302B]">
          {labelUr} <span className="text-xs text-[#5B6F6A]">· {labelEn}</span>
        </p>
        {descUr && <p className="text-xs text-[#5B6F6A]">{descUr}</p>}
      </div>

      {/* Snap Switch */}
      <div
        className={`w-14 h-8 flex items-center rounded-full p-1 transition-colors duration-200 ease-in-out shrink-0 ${
          checked ? "bg-[#1F8A5B]" : "bg-[#E2DDD3]"
        }`}
      >
        <div
          className={`bg-white w-6 h-6 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${
            checked ? "translate-x-6 rtl:-translate-x-6" : "translate-x-0"
          }`}
        />
      </div>
    </div>
  );
}
