"use client";

import { useEffect, useState } from "react";
import { EdgeGlowDot, pulseFromSlo, type Pulse } from "@/components/EdgeGlow";

interface TwinData {
  kernel: Record<string, Record<string, unknown>>;
  twin_state: Record<string, Record<string, unknown>>;
}

function FidelityBadge({ fidelity }: { fidelity: number }) {
  const ok = fidelity >= 99.9;
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${ok ? "bg-edge-green/20 text-edge-green" : "bg-edge-red/20 text-edge-red"}`}>
      {fidelity.toFixed(2)}% {ok ? "✓" : "⚠"}
    </span>
  );
}

function KVTable({ data, label }: { data: Record<string, unknown>; label: string }) {
  return (
    <div className="bg-nexus-bg border border-nexus-border rounded p-3">
      <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-2">{label}</div>
      <div className="space-y-1">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs">
            <span className="text-nexus-muted">{k}</span>
            <span className="text-nexus-text font-mono">{String(v)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TwinPage() {
  const [data, setData] = useState<TwinData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/twin").then((r) => r.json()).then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading twin state...</div>;

  const kernelEntries = data ? Object.entries(data.kernel) : [];
  const twinEntries = data ? Object.entries(data.twin_state) : [];

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Digital Twin</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Real-time kernel state vs twin reflection</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <EdgeGlowDot pulse={pulseFromSlo(99.9973)} size="sm" />
          <FidelityBadge fidelity={99.98} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h2 className="text-xs font-bold text-edge-green uppercase tracking-wider mb-3">Kernel State</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {kernelEntries.map(([name, state]) => (
              <KVTable key={name} data={state as Record<string, unknown>} label={name} />
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-bold text-edge-yellow uppercase tracking-wider mb-3">Twin Reflection</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {twinEntries.map(([name, state]) => (
              <KVTable key={name} data={state as Record<string, unknown>} label={name} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
