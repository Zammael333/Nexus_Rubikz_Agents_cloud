"use client";

import { useEffect, useState } from "react";

interface Recovery {
  id: string;
  worker: string;
  triggered_at: string;
  recovered_at: string;
  downtime_minutes: number;
  rto_met: boolean;
  cause: string;
  action: string;
}

export default function PhoenixHistoryPage() {
  const [recoveries, setRecoveries] = useState<Recovery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/phoenix-history").then((r) => r.json()).then((d) => { setRecoveries(d.recoveries); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading Phoenix history...</div>;

  const avgRTO = recoveries.length > 0
    ? recoveries.reduce((s, r) => s + r.downtime_minutes, 0) / recoveries.length
    : 0;
  const rtoMetCount = recoveries.filter((r) => r.rto_met).length;
  const rtoPct = recoveries.length > 0 ? ((rtoMetCount / recoveries.length) * 100).toFixed(0) : "0";

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Phoenix Protocol History</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Automatic recovery timeline with RTO measurement</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-nexus-text font-mono">{recoveries.length}</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Total Recoveries</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-green font-mono">{avgRTO.toFixed(1)}m</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">Avg RTO</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-green font-mono">{rtoPct}%</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">RTO Met</div>
        </div>
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-edge-yellow font-mono">{recoveries.filter((r) => !r.rto_met).length}</div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mt-1">RTO Missed</div>
        </div>
      </div>

      <div className="relative">
        <div className="absolute left-8 top-0 bottom-0 w-px bg-nexus-border" />

        {recoveries.slice(-20).reverse().map((rec) => (
          <div key={rec.id} className="relative pl-16 pb-5 last:pb-0">
            <div className={`absolute left-5 top-1 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[9px] ${
              rec.rto_met
                ? "bg-edge-green/20 border-edge-green text-edge-green"
                : "bg-edge-red/20 border-edge-red text-edge-red"
            }`}>
              {rec.rto_met ? "✓" : "✗"}
            </div>

            <div className="bg-nexus-surface border border-nexus-border rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-nexus-text uppercase">{rec.worker}</span>
                  <span className="text-[9px] text-nexus-muted">#{rec.id}</span>
                </div>
                <span className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded ${
                  rec.rto_met ? "bg-edge-green/20 text-edge-green" : "bg-edge-red/20 text-edge-red"
                }`}>
                  {rec.downtime_minutes}m downtime {rec.rto_met ? "(RTO met)" : "(RTO miss)"}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                <div>
                  <span className="text-nexus-muted">Triggered</span>
                  <div className="text-nexus-text font-mono">{new Date(rec.triggered_at).toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-nexus-muted">Recovered</span>
                  <div className="text-nexus-text font-mono">{new Date(rec.recovered_at).toLocaleString()}</div>
                </div>
                <div>
                  <span className="text-nexus-muted">Cause</span>
                  <div className="text-nexus-text">{rec.cause}</div>
                </div>
                <div>
                  <span className="text-nexus-muted">Action</span>
                  <div className="text-nexus-text">{rec.action}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
