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
      className={`p-4 rounded-xl border flex items-center justify-between cursor-pointer transition select-none ${
        checked
          ? "bg-emerald-50/70 border-emerald-300 text-emerald-950"
          : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <div className="space-y-0.5 pe-3">
        <p className="font-bold text-sm text-slate-900 leading-snug">
          {labelUr} <span className="text-xs text-slate-500 font-normal">({labelEn})</span>
        </p>
        {descUr && <p className="text-xs text-slate-500">{descUr}</p>}
      </div>

      {/* Snap Switch */}
      <div
        className={`w-12 h-6 flex items-center rounded-full p-0.5 transition-colors duration-200 ease-in-out shrink-0 ${
          checked ? "bg-emerald-600" : "bg-slate-300"
        }`}
      >
        <div
          className={`bg-white w-5 h-5 rounded-full shadow-sm transform transition-transform duration-200 ease-in-out ${
            checked ? "translate-x-6 rtl:-translate-x-6" : "translate-x-0"
          }`}
        />
      </div>
    </div>
  );
}
