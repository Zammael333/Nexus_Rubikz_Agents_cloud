"use client";

import { useEffect, useState } from "react";

interface BudgetPoint {
  date: string;
  budget_remaining: number;
  budget_consumed: number;
  slo_achieved: number;
}

export default function BudgetPage() {
  const [history, setHistory] = useState<BudgetPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/budget-history").then((r) => r.json()).then((d) => { setHistory(d.history); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading budget history...</div>;

  const latest = history[history.length - 1];
  const rate = history.length > 1
    ? (history[0].budget_remaining - history[history.length - 1].budget_remaining) / history.length
    : 0;
  const daysUntilDepleted = rate > 0 ? Math.floor(latest.budget_remaining / rate) : 999;

  const W = 700;
  const H = 280;
  const pad = { top: 20, right: 20, bottom: 30, left: 50 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;

  const minRem = Math.min(...history.map((h) => h.budget_remaining));
  const maxRem = Math.max(...history.map((h) => h.budget_remaining));
  const range = maxRem - minRem || 0.001;

  function xPos(i: number) {
    return pad.left + (i / (history.length - 1)) * plotW;
  }

  function yPos(val: number) {
    return pad.top + plotH - ((val - minRem) / range) * plotH;
  }

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Error Budget History</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Historical consumption with forward projection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-green font-mono">{latest?.budget_remaining.toFixed(4)}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Budget Remaining</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-orange font-mono">{latest?.budget_consumed.toFixed(4)}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Latest Consumption</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-yellow font-mono">{latest?.slo_achieved.toFixed(4)}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Latest SLO</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className={`text-2xl font-bold font-mono ${daysUntilDepleted > 60 ? "text-edge-green" : daysUntilDepleted > 30 ? "text-edge-yellow" : "text-edge-red"}`}>
            ~{daysUntilDepleted}d
          </div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Est. Days to Depletion</div>
        </div>
      </div>

      <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 mb-6">
        <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-4">Budget Burn-Down</h2>
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" style={{ maxHeight: "300px" }}>
          {history.map((h, i) => (
            i % 5 === 0 && (
              <text key={h.date} x={xPos(i)} y={H - 5} textAnchor="middle" fill="#8888aa" fontSize="8">
                {h.date.slice(5)}
              </text>
            )
          ))}

          {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
            const val = minRem + tick * range;
            const y = yPos(val);
            return (
              <g key={tick}>
                <line x1={pad.left} y1={y} x2={W - pad.right} y2={y} stroke="#1e1e3f" strokeWidth="1" />
                <text x={pad.left - 6} y={y + 3} textAnchor="end" fill="#8888aa" fontSize="8">{val.toFixed(4)}</text>
              </g>
            );
          })}

          <polyline
            fill="none"
            stroke="#00ff88"
            strokeWidth="2"
            points={history.map((h, i) => `${xPos(i)},${yPos(h.budget_remaining)}`).join(" ")}
          />

          {history.map((h, i) => (
            i % 5 === 0 && (
              <circle key={h.date} cx={xPos(i)} cy={yPos(h.budget_remaining)} r="3" fill="#00ff88" />
            )
          ))}

          {history.length > 2 && (
            <line
              x1={xPos(history.length - 1)}
              y1={yPos(latest.budget_remaining)}
              x2={xPos(history.length - 1 + 30)}
              y2={yPos(Math.max(0, latest.budget_remaining - rate * 30))}
              stroke="#ff6600"
              strokeWidth="1.5"
              strokeDasharray="4 3"
              opacity="0.6"
            />
          )}
        </svg>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[9px] text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left p-2">Date</th>
              <th className="text-right p-2">Budget Remaining</th>
              <th className="text-right p-2">Consumed</th>
              <th className="text-right p-2">SLO Achieved</th>
            </tr>
          </thead>
          <tbody>
            {history.slice(-15).reverse().map((h) => (
              <tr key={h.date} className="border-b border-nexus-border/50 hover:bg-nexus-bg/50">
                <td className="p-2 text-nexus-muted">{h.date}</td>
                <td className="p-2 text-edge-green text-right font-mono">{h.budget_remaining.toFixed(4)}%</td>
                <td className="p-2 text-edge-yellow text-right font-mono">{h.budget_consumed.toFixed(4)}%</td>
                <td className={`p-2 text-right font-mono ${h.slo_achieved >= 99.997 ? "text-edge-green" : "text-edge-orange"}`}>
                  {h.slo_achieved.toFixed(4)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
