import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          700: "#0B4F43",
          600: "#0F6B5A",
          100: "#DDEFE9",
        },
        accent: {
          DEFAULT: "#E8A33D",
          hover: "#D9942E",
          light: "#FEF3C7",
        },
        paper: "#F7F4EE",
        surface: "#FFFFFF",
        ink: "#17302B",
        muted: "#5B6F6A",
        line: "#E2DDD3",
        ok: "#1F8A5B",
        warn: "#C77700",
        review: "#4C5FD5",
        danger: "#B3261E",
        role: {
          citizen: "#0B4F43",
          helper: "#0284C7",
          officer: "#4C5FD5",
          admin: "#D97706",
          auditor: "#475569",
        },
      },
      fontFamily: {
        sans: ["var(--font-naskh)", "var(--font-inter)", "system-ui", "sans-serif"],
        heading: ["var(--font-nastaliq)", "var(--font-naskh)", "serif"],
        body: ["var(--font-naskh)", "var(--font-inter)", "sans-serif"],
        latin: ["var(--font-inter)", "sans-serif"],
      },
      boxShadow: {
        DEFAULT: "0 6px 20px -6px rgba(11,79,67,0.12), 0 2px 6px rgba(23,48,43,0.04)",
        lift: "0 16px 36px -10px rgba(11,79,67,0.22)",
        glow: "0 0 24px -4px rgba(232,163,61,0.45)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        drawPath: {
          "0%": { strokeDashoffset: "100" },
          "100%": { strokeDashoffset: "0" },
        },
        pulseStone: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(232,163,61,0.7)" },
          "50%": { boxShadow: "0 0 0 8px rgba(232,163,61,0)" },
        },
      },
      animation: {
        "fade-up": "fadeUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in": "fadeIn 0.25s ease-out both",
        "pulse-stone": "pulseStone 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;
