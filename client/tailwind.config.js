/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Command-console palette — near-black with a cold blue cast.
        ink: {
          900: "#05070b",
          800: "#0a0e16",
          700: "#0f1420",
          600: "#151c2c",
          500: "#1d2740",
        },
        line: "#1f2a3d",
        signal: {
          DEFAULT: "#38e1c4", // teal telemetry accent
          dim: "#1c6f63",
        },
        allow: { DEFAULT: "#2fd47a", glow: "#2fd47a33" },
        flag: { DEFAULT: "#f5b642", glow: "#f5b64233" },
        block: { DEFAULT: "#ff4d5e", glow: "#ff4d5e33" },
        muted: "#7f8ba3",
      },
      fontFamily: {
        sans: [
          "InterVariable",
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "JetBrains Mono",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        "glow-allow": "0 0 0 1px #2fd47a55, 0 0 32px -8px #2fd47a",
        "glow-flag": "0 0 0 1px #f5b64255, 0 0 32px -8px #f5b642",
        "glow-block": "0 0 0 1px #ff4d5e55, 0 0 40px -6px #ff4d5e",
        panel: "0 1px 0 0 #ffffff08 inset, 0 12px 40px -20px #000000cc",
      },
      backgroundImage: {
        grid: "linear-gradient(#ffffff08 1px, transparent 1px), linear-gradient(90deg, #ffffff08 1px, transparent 1px)",
        "radial-fade":
          "radial-gradient(120% 80% at 50% -10%, #16305233 0%, transparent 60%)",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)", opacity: "0" },
          "50%": { opacity: "1" },
          "100%": { transform: "translateY(2400%)", opacity: "0" },
        },
        pulse_ring: {
          "0%,100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.25" } },
      },
      animation: {
        scan: "scan 1.1s ease-in-out infinite",
        "pulse-ring": "pulse_ring 2s ease-in-out infinite",
        blink: "blink 1.4s step-end infinite",
      },
    },
  },
  plugins: [],
};
