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
  const progressPct = total > 1 ? (Math.min(currentStep, total - 1) / (total - 1)) * 100 : 0;

  return (
    <div className={`bg-white rounded-3xl p-4 shadow-sm border border-[#E2DDD3] ${className}`}>
      <div className="relative flex items-center justify-between px-3">
        {/* The amber path line that draws itself */}
        <div className="absolute inset-x-8 top-5 h-1.5 bg-[#E2DDD3] -z-0 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#0B4F43] via-[#E8A33D] to-[#E8A33D] transition-all duration-500 ease-out rounded-full"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {milestones.map((m, idx) => {
          const isCompleted = currentStep > idx;
          const isCurrent = currentStep === idx;

          return (
            <div key={m.id} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-300 ${
                  isCurrent
                    ? "bg-[#0B4F43] text-[#E8A33D] ring-4 ring-[#E8A33D]/40 animate-pulse-stone scale-110 shadow-md"
                    : isCompleted
                    ? "bg-[#1F8A5B] text-white shadow-sm"
                    : "bg-white border-2 border-[#E2DDD3] text-[#5B6F6A]"
                }`}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4 checkmark-draw" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  idx + 1
                )}
              </div>
              <span
                className={`text-xs mt-1.5 font-bold transition ${
                  isCurrent ? "text-[#0B4F43]" : isCompleted ? "text-[#1F8A5B]" : "text-[#5B6F6A]"
                }`}
              >
                {m.labelUr}
              </span>
              <span className="text-[10px] text-[#5B6F6A] hidden sm:block">{m.labelEn}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
