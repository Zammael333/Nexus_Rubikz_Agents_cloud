"use client";

import { useEffect, useState } from "react";
import { EdgeGlowDot, EdgeGlowLabel } from "@/components/EdgeGlow";

interface SLOData {
  slo_target: number;
  slo_current: number;
  error_budget_total: number;
  error_budget_remaining: number;
  error_budget_consumed_24h: number;
  monthly_allowance_failures: number;
  failures_this_month: number;
  budget_history: { date: string; remaining: number }[];
  sli_breakdown: {
    availability: number;
    latency_p99_ms: number;
    throughput_rpm: number;
    error_rate_pct: number;
  };
}

function Gauge({ value, max = 100, label, unit = "%" }: { value: number; max?: number; label: string; unit?: string }) {
  const pct = (value / max) * 100;
  const angle = (pct / 100) * 180;
  const color = pct > 90 ? "#00ff88" : pct > 75 ? "#ffcc00" : "#ff6600";

  return (
    <div className="flex flex-col items-center">
      <svg width="120" height="80" viewBox="0 0 120 80">
        <path d="M 10 70 A 50 50 0 0 1 110 70" fill="none" stroke="#1e1e3f" strokeWidth="8" strokeLinecap="round" />
        <path
          d="M 10 70 A 50 50 0 0 1 110 70"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(angle / 180) * 157} 157`}
        />
      </svg>
      <div className="text-xs font-bold text-nexus-text -mt-2">{value.toFixed(4)}{unit}</div>
      <div className="text-[9px] text-nexus-muted uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}

function MiniBar({ value, max, label, color }: { value: number; max: number; label: string; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-nexus-muted w-24 uppercase tracking-wider">{label}</span>
      <div className="flex-1 h-2 bg-nexus-bg rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[10px] text-nexus-text font-mono w-16 text-right">{value}{typeof value === "number" && label.includes("ms") ? "ms" : "%"}</span>
    </div>
  );
}

export default function SLOPage() {
  const [data, setData] = useState<SLOData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/slo").then((r) => r.json()).then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading SLO dashboard...</div>;
  if (!data) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No data</div>;

  const budgetPct = ((data.error_budget_total - data.error_budget_remaining) / data.error_budget_total) * 100;
  const pulse = data.slo_current >= 99.997 ? "green" : data.slo_current >= 99.99 ? "yellow" : data.slo_current >= 99.97 ? "orange" : "red";

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">SLO Dashboard</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Service Level Objectives & Error Budget</p>
        </div>
        <div className="flex items-center gap-2">
          <EdgeGlowDot pulse={pulse} size="sm" />
          <EdgeGlowLabel pulse={pulse} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-green font-mono">{data.slo_current.toFixed(4)}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Current SLO</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-yellow font-mono">{data.error_budget_remaining.toFixed(4)}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Budget Remaining</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-nexus-text font-mono">{data.monthly_allowance_failures}</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Allowable Fails/Month</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-orange font-mono">{data.failures_this_month}</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Failures This Month</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-4">SLO Gauges</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <Gauge value={data.slo_current} max={100} label="SLO" />
            <Gauge value={data.sli_breakdown.availability} max={100} label="Availability" />
            <Gauge value={100 - data.sli_breakdown.error_rate_pct} max={100} label="Success Rate" />
            <Gauge value={data.error_budget_remaining * 1000} max={2.7} label="Budget Remaining" unit="‰" />
          </div>
        </div>

        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-4">SLI Breakdown</h2>
          <div className="space-y-3">
            <MiniBar value={data.sli_breakdown.availability} max={100} label="Availability" color="#00ff88" />
            <MiniBar value={data.sli_breakdown.latency_p99_ms} max={500} label="P99 Latency" color="#ffcc00" />
            <MiniBar value={data.sli_breakdown.throughput_rpm / 100} max={100} label="Throughput" color="#00ff88" />
            <MiniBar value={data.sli_breakdown.error_rate_pct * 100} max={5} label="Error Rate" color="#ff6600" />
          </div>
        </div>
      </div>

      <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
        <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-4">Error Budget Burn-Down</h2>
        <div className="relative h-40">
          <div className="absolute inset-0 flex items-end">
            {data.budget_history.map((point, i) => {
              const h = (point.remaining / data.error_budget_total) * 100;
              const next = data.budget_history[i + 1];
              const nextH = next ? (next.remaining / data.error_budget_total) * 100 : h;
              const x1 = (i / (data.budget_history.length - 1)) * 100;
              const x2 = ((i + 1) / (data.budget_history.length - 1)) * 100;
              return (
                <svg key={point.date} className="absolute w-full h-full" style={{ zIndex: 1 }}>
                  {next && (
                    <line
                      x1={`${x1}%`} y1={`${100 - h}%`}
                      x2={`${x2}%`} y2={`${100 - nextH}%`}
                      stroke="#00ff88" strokeWidth="2" opacity="0.7"
                    />
                  )}
                </svg>
              );
            })}
            {data.budget_history.map((point, i) => {
              const h = (point.remaining / data.error_budget_total) * 100;
              return (
                <div
                  key={point.date}
                  className="absolute bottom-0 w-3 h-3 rounded-full bg-edge-green border-2 border-nexus-bg"
                  style={{ left: `${(i / (data.budget_history.length - 1)) * 100}%`, bottom: `${h}%`, transform: "translate(-50%, 50%)" }}
                />
              );
            })}
          </div>
        </div>
        <div className="flex justify-between mt-2">
          {data.budget_history.filter((_, i) => i % 2 === 0).map((p) => (
            <span key={p.date} className="text-[8px] text-nexus-muted">{p.date.slice(5)}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
