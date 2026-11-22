"use client";

import React from "react";

interface SectionHeaderProps {
  titleUr: string;
  titleEn: string;
  descUr?: string;
  descEn?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function SectionHeader({
  titleUr,
  titleEn,
  descUr,
  descEn,
  icon,
  action,
}: SectionHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[#E2DDD3] pb-3 mb-2">
      <div className="flex items-start gap-3">
        {icon && (
          <div className="w-10 h-10 rounded-2xl bg-[#DDEFE9] text-[#0B4F43] flex items-center justify-center shrink-0 mt-0.5">
            {icon}
          </div>
        )}
        <div className="space-y-0.5">
          <h2 className="text-xl font-bold text-[#0B4F43] font-heading leading-tight">
            {titleUr} <span className="text-sm font-sans font-normal text-[#5B6F6A]">· {titleEn}</span>
          </h2>
          {(descUr || descEn) && (
            <p className="text-xs text-[#5B6F6A] leading-relaxed">
              {descUr} {descEn && <span className="opacity-80">· {descEn}</span>}
            </p>
          )}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function EmptyState({
  titleUr,
  titleEn,
  descUr,
  action,
}: {
  titleUr: string;
  titleEn: string;
  descUr?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-3xl p-8 border border-[#E2DDD3] text-center space-y-3 shadow-sm">
      <div className="w-16 h-16 rounded-full bg-[#F7F4EE] mx-auto flex items-center justify-center">
        <svg className="w-8 h-8 text-[#5B6F6A]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
          <path d="M6 6h10M6 10h10" />
        </svg>
      </div>
      <p className="text-lg font-bold text-[#17302B]">{titleUr}</p>
      <p className="text-xs text-[#5B6F6A]">{descUr || titleEn}</p>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
