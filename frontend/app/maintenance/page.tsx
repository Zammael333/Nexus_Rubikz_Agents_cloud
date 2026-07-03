"use client";

import { useEffect, useState } from "react";
import type { MaintenanceWindow } from "@/app/api/maintenance/route";

export default function MaintenancePage() {
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/maintenance").then((r) => r.json()).then((d) => { setWindows(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading maintenance windows...</div>;
  if (!windows.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No maintenance windows</div>;

  const statusColor = (s: string) => s === "active" ? "text-edge-yellow" : s === "completed" ? "text-edge-green" : s === "scheduled" ? "text-blue-400" : "text-nexus-muted";

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Maintenance Windows</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Scheduled & active maintenance</p>
      </div>

      <div className="space-y-2">
        {windows.map((mw) => {
          const now = new Date();
          const start = new Date(mw.scheduled_start);
          const end = new Date(mw.scheduled_end);
          const isPast = end < now && mw.status !== "active";

          return (
            <div key={mw.id} className={`bg-nexus-surface border rounded-lg p-3 transition-colors ${mw.status === "active" ? "border-edge-yellow/50" : mw.status === "cancelled" ? "border-nexus-border opacity-60" : "border-nexus-border"}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-nexus-text">{mw.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${statusColor(mw.status)} ${mw.status === "active" ? "bg-edge-yellow/10 border border-edge-yellow/30" : "bg-nexus-border/30 border border-nexus-border"}`}>{mw.status}</span>
                  </div>
                  <div className="text-[10px] text-nexus-muted mb-1">{mw.scope}</div>
                  <div className="text-[10px] text-nexus-muted">
                    <span>Owner: {mw.owner}</span>
                    {" · "}
                    <span>{mw.impact}</span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-[10px] text-nexus-muted">
                    {!isPast ? (
                      <>
                        <div className="text-nexus-text font-mono">{start.toLocaleDateString()}</div>
                        <div className="font-mono">{start.toLocaleTimeString()} — {end.toLocaleTimeString()}</div>
                      </>
                    ) : (
                      <>
                        <div className="font-mono">{start.toLocaleDateString()}</div>
                        <div className="font-mono">{start.toLocaleTimeString()}</div>
                      </>
                    )}
                  </div>
                  {mw.actual_start && (
                    <div className="text-[9px] text-nexus-muted mt-1">Actual: {new Date(mw.actual_start).toLocaleTimeString()}</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
