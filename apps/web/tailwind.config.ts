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
        accent: "#E8A33D",
        paper: "#F7F4EE",
        surface: "#FFFFFF",
        ink: "#17302B",
        muted: "#5B6F6A",
        line: "#E2DDD3",
        ok: "#1F8A5B",
        warn: "#C77700",
        review: "#4C5FD5",
        danger: "#B3261E",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "var(--font-urdu)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        DEFAULT: "0 8px 24px -8px rgba(11,79,67,0.18), 0 2px 6px rgba(23,48,43,0.05)",
        lift: "0 16px 40px -10px rgba(11,79,67,0.28)",
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
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(232,163,61,0.7)" },
          "50%": { boxShadow: "0 0 0 6px rgba(232,163,61,0)" },
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
