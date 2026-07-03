import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        edge: {
          green: "#00ff88",
          yellow: "#ffcc00",
          orange: "#ff6600",
          red: "#ff0033",
        },
        nexus: {
          bg: "#0a0a1a",
          surface: "#12122a",
          border: "#1e1e3f",
          text: "#e0e0f0",
          muted: "#8888aa",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
