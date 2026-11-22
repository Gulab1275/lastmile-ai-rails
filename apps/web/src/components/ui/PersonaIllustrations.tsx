"use client";

import React from "react";

/**
 * 3 Flat inline-SVG Persona Illustrations (Under 2 KB each).
 * Warm, authentic, respectful, built from geometric shapes.
 */

export function WidowParveenIllustration({ size = 80 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0"
      aria-label="Widow Parveen Illustration"
    >
      {/* Background circle */}
      <circle cx="50" cy="50" r="48" fill="#FDF2F8" stroke="#F472B6" strokeWidth="2" strokeDasharray="3 3" />
      {/* Dupatta drape behind */}
      <path
        d="M26 48C24 64 22 84 32 94C42 97 58 97 68 94C78 84 76 64 74 48C70 30 30 30 26 48Z"
        fill="#F472B6"
        fillOpacity="0.85"
      />
      {/* Face */}
      <ellipse cx="50" cy="46" rx="14" ry="17" fill="#FBD5B5" />
      {/* Dupatta forehead wrap */}
      <path d="M36 38C42 33 58 33 64 38C62 31 38 31 36 38Z" fill="#DB2777" />
      {/* Eyes & friendly expression */}
      <ellipse cx="45" cy="45" rx="1.5" ry="2" fill="#17302B" />
      <ellipse cx="55" cy="45" rx="1.5" ry="2" fill="#17302B" />
      <path d="M47 53C49 55 51 55 53 53" stroke="#17302B" strokeWidth="1.5" strokeLinecap="round" />
      {/* Gentle smile & dupatta fold over chest */}
      <path d="M32 76C40 68 60 68 68 76L66 94H34L32 76Z" fill="#FCE7F3" />
      <path d="M38 72L50 86L62 72" stroke="#DB2777" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function ShopkeeperTariqIllustration({ size = 80 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0"
      aria-label="Shopkeeper Tariq Illustration"
    >
      {/* Background circle */}
      <circle cx="50" cy="50" r="48" fill="#FEF3C7" stroke="#F59E0B" strokeWidth="2" strokeDasharray="3 3" />
      {/* Shoulders / Kurta */}
      <path d="M22 92C26 72 35 66 50 66C65 66 74 72 78 92H22Z" fill="#D97706" />
      {/* Kurta collar & pocket */}
      <path d="M46 66V82M54 66V82" stroke="#FEF3C7" strokeWidth="2" />
      <rect x="58" y="74" width="8" height="9" rx="2" fill="#B45309" />
      {/* Face & Ears */}
      <ellipse cx="50" cy="45" rx="16" ry="18" fill="#F6C49A" />
      <circle cx="34" cy="46" r="3.5" fill="#F6C49A" />
      <circle cx="66" cy="46" r="3.5" fill="#F6C49A" />
      {/* Friendly hair / Top cap */}
      <path d="M34 40C35 27 65 27 66 40C63 32 37 32 34 40Z" fill="#17302B" />
      {/* Eyes & Mustache */}
      <circle cx="44" cy="43" r="1.8" fill="#17302B" />
      <circle cx="56" cy="43" r="1.8" fill="#17302B" />
      <path d="M42 50C46 48 50 51 50 51C50 51 54 48 58 50C54 53 46 53 42 50Z" fill="#17302B" />
      <path d="M47 55C49 57 51 57 53 55" stroke="#17302B" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function HelperShaziaIllustration({ size = 80 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0"
      aria-label="Helper Shazia Illustration"
    >
      {/* Background circle */}
      <circle cx="50" cy="50" r="48" fill="#E0F2FE" stroke="#0284C7" strokeWidth="2" strokeDasharray="3 3" />
      {/* Field Worker Coat / Uniform */}
      <path d="M22 92C25 68 36 64 50 64C64 64 75 68 78 92H22Z" fill="#0284C7" />
      {/* Face */}
      <ellipse cx="50" cy="42" rx="14" ry="16" fill="#FBD5B5" />
      {/* Modern headscarf / worker hair */}
      <path d="M36 34C40 25 60 25 64 34C62 28 38 28 36 34Z" fill="#0369A1" />
      {/* Eyes & smile */}
      <circle cx="45" cy="41" r="1.8" fill="#17302B" />
      <circle cx="55" cy="41" r="1.8" fill="#17302B" />
      <path d="M47 48C49 51 51 51 53 48" stroke="#17302B" strokeWidth="1.5" strokeLinecap="round" />
      {/* Shared Smartphone held forward */}
      <g transform="translate(42, 62)">
        <rect x="0" y="0" width="16" height="26" rx="3" fill="#17302B" />
        <rect x="2" y="3" width="12" height="18" rx="1.5" fill="#38BDF8" />
        <circle cx="8" cy="23" r="1" fill="#FFFFFF" />
        {/* Glow screen checkmark */}
        <path d="M5 12L7 14L11 9" stroke="#0B4F43" strokeWidth="1.5" strokeLinecap="round" />
      </g>
    </svg>
  );
}
