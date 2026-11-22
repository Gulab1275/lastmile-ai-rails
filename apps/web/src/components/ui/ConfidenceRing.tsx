"use client";

import React from "react";

interface ConfidenceRingProps {
  confidence: number;
  color?: string;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ConfidenceRing({
  confidence,
  color = "#1F8A5B",
  size = 96,
  strokeWidth = 8,
  label = "اعتماد",
}: ConfidenceRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(confidence, 0), 1);
  const strokeDashoffset = circumference - pct * circumference;

  return (
    <div className="relative inline-flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#E2DDD3" strokeWidth={strokeWidth} fill="transparent" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xl font-bold font-mono leading-none text-[#17302B]">{Math.round(pct * 100)}%</span>
        <span className="text-[10px] text-[#5B6F6A] font-bold mt-0.5">{label}</span>
      </div>
    </div>
  );
}
