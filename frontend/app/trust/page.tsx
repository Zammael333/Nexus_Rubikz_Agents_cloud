"use client";

import { useEffect, useState } from "react";

interface WorkerTrust {
  name: string;
  scores: number[];
}

interface TrustData {
  dates: string[];
  workers: WorkerTrust[];
}

const COLORS = ["#00ff88", "#ffcc00", "#ff6600", "#ff0033", "#00ccff", "#cc66ff", "#ff66cc", "#66ffcc", "#ffaa00", "#66ccff"];

export default function TrustPage() {
  const [data, setData] = useState<TrustData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedWorker, setSelectedWorker] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/trust").then((r) => r.json()).then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading trust scores...</div>;
  if (!data) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No data</div>;

  const filtered = selectedWorker ? data.workers.filter((w) => w.name === selectedWorker) : data.workers;

  const minScore = Math.min(...filtered.flatMap((w) => w.scores));
  const maxScore = Math.max(...filtered.flatMap((w) => w.scores));
  const range = maxScore - minScore || 0.1;

  const W = 600;
  const H = 250;
  const pad = { top: 20, right: 20, bottom: 30, left: 40 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  function xPos(i: number) {
    return pad.left + (i / (data!.dates.length - 1)) * plotW;
  }

  function yPos(score: number) {
    return pad.top + plotH - ((score - minScore) / range) * plotH;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Trust Scores</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Score evolution per worker over 30 days</p>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setSelectedWorker(null)}
            className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-colors ${!selectedWorker ? "bg-edge-green/20 text-edge-green border-edge-green/30" : "text-nexus-muted border-nexus-border"}`}
          >
            All
          </button>
          {data.workers.slice(0, 5).map((w) => (
            <button
              key={w.name}
              onClick={() => setSelectedWorker(w.name)}
              className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-colors ${selectedWorker === w.name ? "bg-edge-green/20 text-edge-green border-edge-green/30" : "text-nexus-muted border-nexus-border"}`}
            >
              {w.name}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 mb-6">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" style={{ maxHeight: "280px" }}>
          {data.dates.map((d, i) => (
            i % 7 === 0 && (
              <text key={d} x={xPos(i)} y={H - 5} textAnchor="middle" fill="#8888aa" fontSize="8">
                {d.slice(5)}
              </text>
            )
          ))}

          {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
            const score = minScore + tick * range;
            const y = yPos(score);
            return (
              <g key={tick}>
                <line x1={pad.left} y1={y} x2={W - pad.right} y2={y} stroke="#1e1e3f" strokeWidth="1" />
                <text x={pad.left - 6} y={y + 3} textAnchor="end" fill="#8888aa" fontSize="8">{(score * 100).toFixed(0)}%</text>
              </g>
            );
          })}

          {filtered.map((worker, wi) => {
            const color = COLORS[wi % COLORS.length];
            const points = worker.scores.map((s, i) => `${xPos(i)},${yPos(s)}`).join(" ");
            return (
              <g key={worker.name}>
                <polyline fill="none" stroke={color} strokeWidth="1.5" opacity="0.8" points={points} />
                {worker.scores.map((s, i) => (
                  i % 5 === 0 && (
                    <circle key={i} cx={xPos(i)} cy={yPos(s)} r="2" fill={color} />
                  )
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {data.workers.map((w, i) => {
          const latest = w.scores[w.scores.length - 1];
          const color = latest >= 0.95 ? "text-edge-green" : latest >= 0.85 ? "text-edge-yellow" : "text-edge-red";
          return (
            <button
              key={w.name}
              onClick={() => setSelectedWorker(selectedWorker === w.name ? null : w.name)}
              className={`bg-nexus-surface border rounded-lg p-3 text-left transition-colors hover:border-nexus-border/80 ${
                selectedWorker === w.name ? "border-edge-green/30 bg-edge-green/5" : "border-nexus-border"
              }`}
            >
              <div className="text-[10px] text-nexus-muted uppercase tracking-wider">{w.name}</div>
              <div className={`text-sm font-bold mt-1 font-mono ${color}`}>{(latest * 100).toFixed(1)}%</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
