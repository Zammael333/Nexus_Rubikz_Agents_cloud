"use client";

import { useEffect, useState } from "react";
import type { AuditEntry } from "@/app/api/audit-trail/route";

export default function AuditTrailPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/audit-trail").then((r) => r.json()).then((d) => { setEntries(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading audit trail...</div>;
  if (!entries.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No audit entries</div>;

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Audit Trail</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Immutable record of all system changes</p>
      </div>

      <div className="space-y-2">
        {entries.map((entry) => (
          <div key={entry.id} className="bg-nexus-surface border border-nexus-border rounded-lg p-3 hover:bg-nexus-border/10 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono text-nexus-muted">{entry.id}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-edge-green/10 text-edge-green border border-edge-green/30">{entry.action}</span>
                  {entry.actor === "system" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">system</span>
                  )}
                </div>
                <div className="text-xs text-nexus-text mb-1">{entry.detail}</div>
                <div className="text-[10px] text-nexus-muted">
                  <span className="font-mono">{entry.actor}</span>
                  {" · "}
                  <span>{entry.resource}</span>
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-[10px] text-nexus-muted font-mono">{new Date(entry.timestamp).toLocaleDateString()}</div>
                <div className="text-[10px] text-nexus-muted font-mono">{new Date(entry.timestamp).toLocaleTimeString()}</div>
                <div className="text-[9px] text-nexus-muted mt-1">{entry.ip_address}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
