"use client";

import { useEffect, useState } from "react";
import type { Incident } from "@/app/api/incidents/route";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<Incident | null>(null);

  useEffect(() => {
    fetch("/api/incidents").then((r) => r.json()).then((d) => { setIncidents(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading incidents...</div>;
  if (!incidents.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No incidents</div>;

  const sevColor = (s: string) => s === "SEV1" ? "text-edge-orange" : s === "SEV2" ? "text-edge-yellow" : "text-nexus-muted";
  const statusColor = (s: string) => s === "open" ? "text-edge-orange" : s === "investigating" ? "text-edge-yellow" : s === "mitigated" ? "text-blue-400" : "text-edge-green";

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Incidents</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Incident management timeline</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-edge-orange px-2 py-1 rounded bg-edge-orange/10 border border-edge-orange/30">{incidents.filter((i) => i.status === "open").length} open</span>
          <span className="text-[10px] text-edge-green px-2 py-1 rounded bg-edge-green/10 border border-edge-green/30">{incidents.filter((i) => i.status === "resolved").length} resolved</span>
        </div>
      </div>

      <div className="space-y-2">
        {incidents.map((inc) => (
          <div
            key={inc.id}
            className="bg-nexus-surface border border-nexus-border rounded-lg p-3 hover:bg-nexus-border/10 transition-colors cursor-pointer"
            onClick={() => setDetail(detail?.id === inc.id ? null : inc)}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-bold font-mono ${sevColor(inc.severity)}`}>{inc.severity}</span>
                  <span className="text-xs font-bold text-nexus-text">{inc.title}</span>
                  <span className={`text-[10px] font-mono ${statusColor(inc.status)}`}>{inc.status}</span>
                </div>
                <div className="text-[10px] text-nexus-muted">
                  <span>Affected: {inc.affected_workers.join(", ")}</span>
                </div>
                {detail?.id === inc.id && (
                  <div className="mt-2 p-2 bg-nexus-bg rounded border border-nexus-border">
                    <p className="text-xs text-nexus-text mb-1">{inc.summary}</p>
                    <div className="text-[10px] text-nexus-muted space-y-0.5">
                      <div>Detected: {new Date(inc.detected_at).toLocaleString()}</div>
                      {inc.acknowledged_at && <div>Acknowledged: {new Date(inc.acknowledged_at).toLocaleString()}</div>}
                      {inc.resolved_at && <div>Resolved: {new Date(inc.resolved_at).toLocaleString()}</div>}
                    </div>
                  </div>
                )}
              </div>
              <div className="text-right shrink-0">
                <div className="text-[10px] text-nexus-muted font-mono">{new Date(inc.detected_at).toLocaleDateString()}</div>
                <div className="text-[10px] text-nexus-muted font-mono">{new Date(inc.detected_at).toLocaleTimeString()}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
