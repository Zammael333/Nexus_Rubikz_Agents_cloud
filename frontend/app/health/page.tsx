"use client";

import { useEffect, useState } from "react";
import { EdgeGlowDot, EdgeGlowLabel, type Pulse } from "@/components/EdgeGlow";
import WorkerDetailModal from "@/components/WorkerDetailModal";
import PhoenixControl from "@/components/PhoenixControl";
import BudgetControl from "@/components/BudgetControl";

interface WorkerHealth {
  id: string;
  label: string;
  status: string;
  pulse: Pulse;
  uptime: string;
  cpu: number;
  memory: number;
  latency_ms: number;
  last_check: string;
  trust_score: number;
  sandbox?: boolean;
  phoenix?: boolean;
  budget_frozen?: boolean;
}

function HealthBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: pct > 80 ? "#ff6600" : pct > 60 ? "#ffcc00" : "#00ff88" }} />
    </div>
  );
}

export default function HealthPage() {
  const [workers, setWorkers] = useState<WorkerHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorker, setSelectedWorker] = useState<WorkerHealth | null>(null);
  const [frozen, setFrozen] = useState(false);

  const fetchWorkers = () => fetch("/api/health").then((r) => r.json()).then((d) => { setWorkers(d.workers); setLoading(false); });

  useEffect(() => { fetchWorkers(); }, []);

  const handleRestart = async (workerId: string) => {
    await new Promise((r) => setTimeout(r, 500));
  };

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading health data...</div>;

  const healthy = workers.filter((w) => w.status === "healthy").length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Health Dashboard</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Click a card for worker detail</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-nexus-muted uppercase tracking-wider">{healthy}/{workers.length} healthy</span>
            <EdgeGlowDot pulse={healthy === workers.length ? "green" : healthy >= workers.length - 2 ? "yellow" : "orange"} size="sm" />
          </div>
        </div>
      </div>

      <div className="mb-6">
        <BudgetControl onFreeze={() => setFrozen(true)} onThaw={() => setFrozen(false)} frozen={frozen} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {workers.map((w) => (
          <div
            key={w.id}
            onClick={() => setSelectedWorker(w)}
            className="bg-nexus-surface border border-nexus-border rounded-lg p-4 hover:border-nexus-border/80 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <EdgeGlowDot pulse={w.pulse} size="sm" />
                <span className="text-xs font-bold text-nexus-text uppercase tracking-wider">{w.label}</span>
                {w.sandbox && (
                  <span className="text-[9px] uppercase tracking-wider px-1 py-0.5 rounded border bg-edge-yellow/20 text-edge-yellow border-edge-yellow/30">Sandbox</span>
                )}
              </div>
              <EdgeGlowLabel pulse={w.pulse} />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Status</span>
                <span className="text-nexus-text">{w.status}</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Uptime</span>
                <span className="text-nexus-text">{w.uptime}</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">CPU</span>
                <span className="text-nexus-text">{w.cpu}%</span>
              </div>
              <HealthBar value={w.cpu} />
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Memory</span>
                <span className="text-nexus-text">{w.memory}%</span>
              </div>
              <HealthBar value={w.memory} />
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Latency</span>
                <span className="text-nexus-text">{w.latency_ms}ms</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Trust Score</span>
                <span className="text-nexus-text">{(w.trust_score * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">Last Check</span>
                <span className="text-nexus-text">{new Date(w.last_check).toLocaleTimeString()}</span>
              </div>
            </div>

            {w.phoenix && (
              <PhoenixControl workerId={w.id} workerLabel={w.label} onRestart={handleRestart} />
            )}
          </div>
        ))}
      </div>

      <WorkerDetailModal worker={selectedWorker} onClose={() => setSelectedWorker(null)} />
    </div>
  );
}
