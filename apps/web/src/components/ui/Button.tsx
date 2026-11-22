"use client";

import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "neutral" | "danger" | "quiet" | "outline";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "font-bold rounded-2xl transition inline-flex items-center justify-center gap-2 select-none min-h-[48px] active:scale-[0.98]";

  const sizes = {
    sm: "px-3 py-2 text-xs min-h-[40px]",
    md: "px-5 py-3 text-sm min-h-[48px]",
    lg: "px-6 py-3.5 text-base min-h-[54px]",
  };

  const variants = {
    // Single primary action per screen: Amber #E8A33D with dark ink text #17302B
    primary:
      "bg-[#E8A33D] text-[#17302B] hover:bg-[#D9942E] shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    secondary:
      "bg-[#0B4F43] text-white hover:bg-[#093e34] shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    neutral:
      "bg-white border-2 border-[#E2DDD3] text-[#17302B] hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none",
    outline:
      "bg-white border-2 border-[#E2DDD3] text-[#17302B] hover:bg-slate-50 disabled:opacity-40 disabled:pointer-events-none",
    danger:
      "bg-white border-2 border-[#B3261E] text-[#B3261E] hover:bg-[#FEE2E2] disabled:opacity-40 disabled:pointer-events-none",
    quiet:
      "bg-transparent text-[#0B4F43] hover:bg-[#DDEFE9]/50 disabled:opacity-40 disabled:pointer-events-none",
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span>لوڈ ہو رہا ہے...</span>
        </span>
      ) : (
        children
      )}
    </button>
  );
}
