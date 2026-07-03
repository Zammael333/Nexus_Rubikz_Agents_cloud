"use client";

import { useEffect, useState } from "react";

type Pulse = "green" | "yellow" | "orange" | "red";

const PULSE_COLORS: Record<Pulse, string> = {
  green: "bg-edge-green shadow-[0_0_20px_rgba(0,255,136,0.5)]",
  yellow: "bg-edge-yellow shadow-[0_0_20px_rgba(255,204,0,0.5)]",
  orange: "bg-edge-orange shadow-[0_0_20px_rgba(255,102,0,0.5)]",
  red: "bg-edge-red shadow-[0_0_20px_rgba(255,0,51,0.5)]",
};

const PULSE_ORDER: Pulse[] = ["green", "yellow", "orange", "red"];

export default function Home() {
  const [pulse, setPulse] = useState<Pulse>("green");
  const [slo, setSlo] = useState<number>(99.9973);
  const [errorBudget, setErrorBudget] = useState<number>(0.0027);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/pulse");
        const data = await res.json();
        setPulse(data.pulse ?? "green");
        setSlo(data.slo?.real_slo ?? 99.9973);
        setErrorBudget(data.slo?.error_budget_remaining ?? 0.0027);
      } catch {
        // fallback cycler when API is unavailable
        setPulse((p) => PULSE_ORDER[(PULSE_ORDER.indexOf(p) + 1) % PULSE_ORDER.length]);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <h1 className="text-3xl font-bold tracking-widest uppercase text-nexus-text">
        NEXUS<span className="text-edge-green">RUBYKZ</span>
      </h1>

      <div className="text-sm text-nexus-muted tracking-widest uppercase">
        Edge Glow · System Pulse
      </div>

      <div className={`w-32 h-32 rounded-full transition-all duration-700 ${PULSE_COLORS[pulse]}`} />

      <div className="text-xl font-semibold tracking-widest uppercase">
        <span className={pulse === "green" ? "text-edge-green" : pulse === "yellow" ? "text-edge-yellow" : pulse === "orange" ? "text-edge-orange" : "text-edge-red"}>
          {pulse}
        </span>
      </div>

      <div className="flex gap-12 text-sm">
        <div className="text-center">
          <div className="text-nexus-muted uppercase tracking-wider">SLO</div>
          <div className="text-lg font-semibold text-edge-green">{slo.toFixed(4)}%</div>
        </div>
        <div className="text-center">
          <div className="text-nexus-muted uppercase tracking-wider">Error Budget</div>
          <div className="text-lg font-semibold text-edge-yellow">{errorBudget.toFixed(4)}%</div>
        </div>
      </div>

      <div className="text-xs text-nexus-muted mt-8 border-t border-nexus-border pt-4 w-full max-w-sm text-center">
        NEXUS-RUBYKZ v0.1 · SLO 99.9973%
      </div>
    </main>
  );
}
