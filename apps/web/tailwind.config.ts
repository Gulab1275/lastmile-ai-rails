import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        // Latin letters use Inter; Urdu falls through to Noto Nastaliq.
        sans: ["var(--font-inter)", "var(--font-urdu)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        // Every existing "shadow" card gets a softer, green-tinted shadow.
        DEFAULT: "0 8px 24px -8px rgba(5,150,105,0.22), 0 2px 6px rgba(15,23,42,0.06)",
        lift: "0 16px 40px -10px rgba(5,150,105,0.35)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        pulseDot: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(52,211,153,0.7)" },
          "50%": { boxShadow: "0 0 0 6px rgba(52,211,153,0)" },
        },
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out both",
        float: "float 6s ease-in-out infinite",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;