/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f5ebf5",
          100: "#e8c8e8",
          200: "#d4a8d4",
          300: "#c88bc8",
          400: "#b574b5",
          500: "#a262a2",
          600: "#7a457a",
          700: "#5c335c",
          800: "#3d223d",
          900: "#241424",
          950: "#120a12",
        },
        void: {
          DEFAULT: "#070509",
          50: "#110d13",
          100: "#161019",
          200: "#1c1420",
        },
      },
      fontFamily: {
        dyslexic: ['"OpenDyslexic"', "sans-serif"],
        terminal: ['"Share Tech Mono"', "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(162, 98, 162, 0.35)",
        "glow-lg": "0 0 40px rgba(162, 98, 162, 0.45)",
        crt: "inset 0 0 80px rgba(162, 98, 162, 0.08)",
      },
      animation: {
        glitch: "glitch 2.5s infinite",
        flicker: "flicker 4s infinite",
        scan: "scan 8s linear infinite",
        blink: "blink 1.2s step-end infinite",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
      },
      keyframes: {
        glitch: {
          "0%, 100%": { transform: "translate(0)" },
          "20%": { transform: "translate(-2px, 1px)" },
          "40%": { transform: "translate(2px, -1px)" },
          "60%": { transform: "translate(-1px, -1px)" },
          "80%": { transform: "translate(1px, 1px)" },
        },
        flicker: {
          "0%, 100%": { opacity: "1" },
          "92%": { opacity: "1" },
          "93%": { opacity: "0.85" },
          "94%": { opacity: "1" },
          "97%": { opacity: "0.9" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(162, 98, 162, 0.25)" },
          "50%": { boxShadow: "0 0 35px rgba(162, 98, 162, 0.5)" },
        },
      },
    },
  },
  plugins: [],
};
