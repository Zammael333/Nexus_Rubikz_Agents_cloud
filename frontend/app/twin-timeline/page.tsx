"use client";

import { useEffect, useState } from "react";

interface TimelineEntry {
  timestamp: string;
  kernel: Record<string, Record<string, unknown>>;
  twin: Record<string, Record<string, unknown>>;
  diff_count: number;
}

function DiffTag() {
  return (
    <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-edge-red/20 text-edge-red border border-edge-red/30">
      DIFF
    </span>
  );
}

function MatchTag() {
  return (
    <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-edge-green/20 text-edge-green border border-edge-green/30">
      MATCH
    </span>
  );
}

export default function TwinTimelinePage() {
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/twin-timeline").then((r) => r.json()).then((d) => { setEntries(d.timeline); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading twin timeline...</div>;

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Twin Timeline</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Kernel vs Twin state evolution with diff markers</p>
      </div>

      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-px bg-nexus-border" />

        {entries.map((entry, i) => {
          const isDiff = entry.diff_count > 0;
          return (
            <div key={entry.timestamp} className="relative pl-16 pb-6 last:pb-0">
              <div className={`absolute left-4 top-1 w-4 h-4 rounded-full border-2 ${isDiff ? "bg-edge-red border-edge-red" : "bg-edge-green border-edge-green"}`} />

              <div className={`bg-nexus-surface border rounded-lg p-4 ${isDiff ? "border-edge-red/30" : "border-nexus-border"}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-nexus-muted font-mono">{new Date(entry.timestamp).toLocaleString()}</span>
                    {isDiff ? <DiffTag /> : <MatchTag />}
                  </div>
                  {isDiff && <span className="text-[10px] text-edge-red">{entry.diff_count} divergence(s)</span>}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-[10px] text-edge-green uppercase tracking-wider mb-2">Kernel</div>
                    {Object.entries(entry.kernel).map(([mod, state]) => (
                      <div key={mod} className="text-[10px] text-nexus-text mb-1">
                        <span className="text-nexus-muted">{mod}:</span>{" "}
                        {Object.entries(state as Record<string, unknown>).map(([k, v]) => `${k}=${v}`).join(", ")}
                      </div>
                    ))}
                  </div>
                  <div>
                    <div className="text-[10px] text-edge-yellow uppercase tracking-wider mb-2">Twin</div>
                    {Object.entries(entry.twin).map(([mod, state]) => (
                      <div key={mod} className="text-[10px] text-nexus-text mb-1">
                        <span className="text-nexus-muted">{mod}:</span>{" "}
                        {Object.entries(state as Record<string, unknown>).map(([k, v]) => `${k}=${v}`).join(", ")}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
