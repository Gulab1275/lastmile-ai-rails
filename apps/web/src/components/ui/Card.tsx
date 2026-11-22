"use client";

import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "brand" | "accent" | "highlight" | "danger";
}

export function Card({ children, variant = "default", className = "", ...props }: CardProps) {
  const variants = {
    default: "bg-white border border-[#E2DDD3] text-[#17302B]",
    brand: "bg-[#DDEFE9] border-2 border-[#1F8A5B] text-[#065F46]",
    accent: "bg-[#FEF3C7] border-2 border-[#C77700] text-[#92400E]",
    highlight: "bg-[#EEF2FF] border-2 border-[#4C5FD5] text-[#1E1B4B]",
    danger: "bg-[#FEE2E2] border-2 border-[#B3261E] text-[#7F1D1D]",
  };

  return (
    <div className={`rounded-3xl shadow-sm p-5 transition ${variants[variant]} ${className}`} {...props}>
      {children}
    </div>
  );
}
