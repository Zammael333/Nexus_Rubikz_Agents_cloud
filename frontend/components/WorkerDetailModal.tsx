"use client";

import { EdgeGlowDot, EdgeGlowLabel, type Pulse } from "@/components/EdgeGlow";
import Modal from "@/components/Modal";

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
  last_executions?: string[];
  config?: Record<string, string>;
}

interface WorkerDetailModalProps {
  worker: WorkerHealth | null;
  onClose: () => void;
}

function HealthBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${pct}%`, background: pct > 80 ? "#ff6600" : pct > 60 ? "#ffcc00" : "#00ff88" }}
      />
    </div>
  );
}

export default function WorkerDetailModal({ worker, onClose }: WorkerDetailModalProps) {
  if (!worker) return null;

  const mockExecutions = worker.last_executions ?? [
    "heartbeat check",
    "cache purge",
    "sync twin state",
    "process event queue",
    "health report",
  ];

  const mockConfig = worker.config ?? {
    pool_size: "4",
    timeout_ms: "5000",
    retry_policy: "exponential",
    log_level: "info",
    region: "us-east-1",
  };

  return (
    <Modal open={!!worker} onClose={onClose} title="Worker Detail" width="w-[32rem]">
      <div className="space-y-4 font-mono">
        <div className="flex items-center gap-2">
          <EdgeGlowDot pulse={worker.pulse} size="sm" />
          <span className="text-sm font-bold text-nexus-text uppercase tracking-wider">{worker.label}</span>
          {worker.sandbox && (
            <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border bg-edge-yellow/20 text-edge-yellow border-edge-yellow/30">
              Sandbox
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Status</div>
            <EdgeGlowLabel pulse={worker.pulse} />
          </div>
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Uptime</div>
            <div className="text-xs text-nexus-text">{worker.uptime}</div>
          </div>
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">CPU</div>
            <div className="text-xs text-nexus-text mb-1">{worker.cpu}%</div>
            <HealthBar value={worker.cpu} />
          </div>
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Memory</div>
            <div className="text-xs text-nexus-text mb-1">{worker.memory}%</div>
            <HealthBar value={worker.memory} />
          </div>
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Latency</div>
            <div className="text-xs text-nexus-text">{worker.latency_ms}ms</div>
          </div>
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Trust Score</div>
            <div className="text-xs text-nexus-text mb-1">{(worker.trust_score * 100).toFixed(0)}%</div>
            <HealthBar value={worker.trust_score * 100} />
          </div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Last Check</div>
          <div className="text-xs text-nexus-text">{new Date(worker.last_check).toLocaleString()}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-2">Last Executions</div>
          <div className="space-y-1">
            {mockExecutions.map((action, i) => (
              <div key={i} className="flex items-center gap-2 text-[10px] text-nexus-text bg-nexus-bg border border-nexus-border rounded px-2 py-1">
                <span className="text-nexus-muted">{i + 1}.</span>
                <span className="uppercase tracking-wider">{action}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-2">Config</div>
          <div className="bg-nexus-bg border border-nexus-border rounded p-2 space-y-1">
            {Object.entries(mockConfig).map(([key, val]) => (
              <div key={key} className="flex justify-between text-[10px]">
                <span className="text-nexus-muted">{key}</span>
                <span className="text-nexus-text">{val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
