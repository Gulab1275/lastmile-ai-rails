"use client";

import React from "react";

export interface StepMilestone {
  id: number;
  labelUr: string;
  labelEn: string;
}

const DEFAULT_MILESTONES: StepMilestone[] = [
  { id: 0, labelUr: "شناخت", labelEn: "Identify" },
  { id: 1, labelUr: "کاغذات", labelEn: "Documents" },
  { id: 2, labelUr: "جانچ", labelEn: "Check" },
  { id: 3, labelUr: "فیصلہ", labelEn: "Decision" },
  { id: 4, labelUr: "ادائیگی", labelEn: "Payment" },
];

interface StepStonesProps {
  currentStep: number; // 0 to 4
  milestones?: StepMilestone[];
  className?: string;
}

export function StepStones({
  currentStep,
  milestones = DEFAULT_MILESTONES,
  className = "",
}: StepStonesProps) {
  const total = milestones.length;
  const currentMilestone = milestones[Math.min(currentStep, total - 1)] ?? milestones[0];

  return (
    <div className={`bg-white rounded-2xl p-4 border border-slate-200 shadow-sm ${className}`}>
      {/* Mobile clean summary header */}
      <div className="flex sm:hidden items-center justify-between pb-2 mb-2 border-b border-slate-100 text-xs">
        <span className="font-bold text-[#0B4F43]">
          مرحلہ {currentStep + 1} از {total}
        </span>
        <span className="font-medium text-slate-700">
          {currentMilestone.labelUr} ({currentMilestone.labelEn})
        </span>
      </div>

      {/* Progress Track */}
      <div className="relative flex items-center justify-between px-2 pt-1 pb-1">
        <div className="absolute inset-x-6 top-5 h-1 bg-slate-200 -z-0 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0B4F43] transition-all duration-500 ease-out rounded-full"
            style={{ width: `${(Math.min(currentStep, total - 1) / (total - 1)) * 100}%` }}
          />
        </div>

        {milestones.map((m, idx) => {
          const isCompleted = currentStep > idx;
          const isCurrent = currentStep === idx;

          return (
            <div key={m.id} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${
                  isCurrent
                    ? "bg-[#0B4F43] text-white ring-4 ring-[#0B4F43]/20 shadow"
                    : isCompleted
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "bg-white border-2 border-slate-300 text-slate-500"
                }`}
              >
                {isCompleted ? "✓" : idx + 1}
              </div>
              <span
                className={`text-xs mt-1.5 font-medium transition hidden sm:block ${
                  isCurrent ? "font-bold text-[#0B4F43]" : isCompleted ? "text-emerald-700" : "text-slate-500"
                }`}
              >
                {m.labelUr}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
