import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          900: "#06322B",
          800: "#084137",
          700: "#0B4F43",
          600: "#0F6B5A",
          100: "#E6F4F1",
          50: "#F0F9F7",
        },
        accent: {
          DEFAULT: "#D97706",
          hover: "#B45309",
          light: "#FEF3C7",
          50: "#FFFBEB",
        },
        paper: "#F8FAFC",
        surface: "#FFFFFF",
        ink: "#0F172A",
        muted: "#475569",
        line: "#E2E8F0",
        ok: "#059669",
        warn: "#D97706",
        review: "#4F46E5",
        danger: "#DC2626",
      },
      fontFamily: {
        sans: ["var(--font-naskh)", "var(--font-inter)", "system-ui", "sans-serif"],
        heading: ["var(--font-naskh)", "var(--font-inter)", "sans-serif"],
        body: ["var(--font-naskh)", "var(--font-inter)", "sans-serif"],
        latin: ["var(--font-inter)", "sans-serif"],
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
        DEFAULT: "0 1px 3px 0 rgba(15, 23, 42, 0.08), 0 1px 2px -1px rgba(15, 23, 42, 0.08)",
        md: "0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.06)",
        lg: "0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)",
        lift: "0 12px 24px -6px rgba(11, 79, 67, 0.15)",
      },
    },
  },
  plugins: [],
};
export default config;
