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
    "font-bold rounded-xl transition inline-flex items-center justify-center gap-2 select-none active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-[#0B4F43] leading-normal";

  const sizes = {
    sm: "px-3.5 py-2 text-xs min-h-[38px]",
    md: "px-5 py-2.5 text-sm min-h-[46px]",
    lg: "px-6 py-3 text-base min-h-[52px]",
  };

  const variants = {
    primary:
      "bg-[#D97706] text-slate-900 hover:bg-[#B45309] hover:text-white shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    secondary:
      "bg-[#0B4F43] text-white hover:bg-[#084137] shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    neutral:
      "bg-white border border-slate-300 text-slate-800 hover:bg-slate-50 hover:border-slate-400 shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    outline:
      "bg-white border border-slate-300 text-slate-800 hover:bg-slate-50 hover:border-slate-400 shadow-sm disabled:opacity-40 disabled:pointer-events-none",
    danger:
      "bg-white border border-rose-300 text-rose-700 hover:bg-rose-50 disabled:opacity-40 disabled:pointer-events-none",
    quiet:
      "bg-transparent text-[#0B4F43] hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none",
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span>{children}</span>
        </span>
      ) : (
        children
      )}
    </button>
  );
}
