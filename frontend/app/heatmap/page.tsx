"use client";

import { useEffect, useState } from "react";

interface CellValues {
  cpu: number;
  memory: number;
  latency: number;
  errors: number;
}

interface HourData {
  hour: string;
  cells: Record<string, CellValues>;
}

interface HeatmapData {
  workers: string[];
  metrics: string[];
  hours: string[];
  data: HourData[];
}

function heatColor(value: number, metric: string): string {
  let pct: number;
  if (metric === "errors") {
    pct = Math.min(value / 10, 1);
  } else if (metric === "latency") {
    pct = Math.min(value / 400, 1);
  } else {
    pct = Math.min(value / 100, 1);
  }
  if (pct < 0.3) return `rgba(0, 255, 136, ${0.15 + pct * 0.5})`;
  if (pct < 0.6) return `rgba(255, 204, 0, ${0.2 + pct * 0.5})`;
  return `rgba(255, 0, 51, ${0.2 + pct * 0.6})`;
}

export default function HeatmapPage() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState("cpu");

  useEffect(() => {
    fetch("/api/heatmap").then((r) => r.json()).then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading heatmap...</div>;
  if (!data) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No data</div>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Worker Heatmap</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">CPU · Memory · Latency · Errors per worker over 24h</p>
        </div>
        <div className="flex gap-1">
          {data.metrics.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedMetric(m)}
              className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-colors ${
                selectedMetric === m
                  ? "bg-edge-green/20 text-edge-green border-edge-green/30"
                  : "text-nexus-muted border-nexus-border hover:text-nexus-text"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="grid gap-0 min-w-[600px]" style={{ gridTemplateColumns: `100px repeat(${data.hours.length}, 1fr)` }}>
          <div className="text-[9px] text-nexus-muted uppercase tracking-wider p-1" />

          {data.hours.filter((_, i) => i % 3 === 0).map((h) => (
            <div key={h} className="text-[8px] text-nexus-muted text-center p-1">{h.slice(0, 2)}</div>
          ))}

          {data.workers.map((worker) => (
            <>
              <div className="text-[9px] text-nexus-muted p-1 truncate">{worker}</div>
              {data.data.map((hourData) => {
                const val = hourData.cells[worker]?.[selectedMetric as keyof CellValues] ?? 0;
                return (
                  <div
                    key={`${worker}-${hourData.hour}`}
                    className="h-6 flex items-center justify-center text-[8px] text-nexus-text font-mono"
                    style={{ backgroundColor: heatColor(val, selectedMetric) }}
                    title={`${worker} @ ${hourData.hour}: ${val}${selectedMetric === "latency" ? "ms" : selectedMetric === "errors" ? "" : "%"}`}
                  >
                    {val}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <span className="text-[10px] text-nexus-muted uppercase tracking-wider">Legend:</span>
        {[{ label: "Low", color: "rgba(0,255,136,0.4)" }, { label: "Medium", color: "rgba(255,204,0,0.5)" }, { label: "High", color: "rgba(255,0,51,0.6)" }].map((l) => (
          <div key={l.label} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded inline-block" style={{ backgroundColor: l.color }} />
            <span className="text-[9px] text-nexus-muted">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
