"use client";

import { useEffect, useState } from "react";
import type { TopologyData } from "@/app/api/topology/route";

export default function TopologyPage() {
  const [data, setData] = useState<TopologyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/topology").then((r) => r.json()).then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading topology...</div>;
  if (!data) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No topology data</div>;

  const typeColor = (t: string) => t === "service" ? "border-edge-green text-edge-green" : t === "worker" ? "border-blue-400 text-blue-400" : t === "database" ? "border-edge-yellow text-edge-yellow" : t === "external" ? "border-nexus-muted text-nexus-muted" : "border-edge-orange text-edge-orange";
  const statusBg = (s: string) => s === "healthy" ? "bg-edge-green/10" : s === "degraded" ? "bg-edge-yellow/10" : "bg-edge-orange/10";

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Service Topology</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Dependency graph & service health</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-3">Nodes</h2>
          <div className="space-y-2">
            {data.nodes.map((n) => {
              const edges = data.edges.filter((e) => e.source === n.id || e.target === n.id);
              const avgLatency = edges.length ? Math.round(edges.reduce((a, e) => a + e.latency_p99_ms, 0) / edges.length) : 0;
              return (
                <div
                  key={n.id}
                  className={`bg-nexus-surface border rounded-lg p-3 cursor-pointer transition-all ${selected === n.id ? "ring-1 ring-edge-green border-edge-green/50" : "border-nexus-border"} ${statusBg(n.status)}`}
                  onClick={() => setSelected(selected === n.id ? null : n.id)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-nexus-text">{n.name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${typeColor(n.type)}`}>{n.type}</span>
                    </div>
                    <span className={`text-[10px] font-mono ${n.status === "healthy" ? "text-edge-green" : n.status === "degraded" ? "text-edge-yellow" : "text-edge-orange"}`}>{n.status}</span>
                  </div>
                  {selected === n.id && (
                    <div className="mt-2 text-[10px] text-nexus-muted">
                      <div>Dependencies: {n.dependencies.length ? n.dependencies.join(", ") : "None"}</div>
                      <div>Connections: {edges.length} ({avgLatency}ms avg p99)</div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-3">Edges</h2>
          <div className="space-y-2">
            {data.edges.map((e, i) => {
              const sourceNode = data.nodes.find((n) => n.id === e.source);
              const targetNode = data.nodes.find((n) => n.id === e.target);
              return (
                <div key={i} className="bg-nexus-surface border border-nexus-border rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-nexus-text">{e.source}</span>
                    <span className="text-[10px] text-nexus-muted">→</span>
                    <span className="text-xs font-mono text-nexus-text">{e.target}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-nexus-muted">
                    <span>{e.protocol}</span>
                    <span>{e.latency_p99_ms}ms p99</span>
                    <span className={e.error_rate_pct > 1 ? "text-edge-orange" : "text-edge-green"}>{e.error_rate_pct}% err</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
