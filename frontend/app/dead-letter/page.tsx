"use client";

import { useEffect, useState } from "react";

interface DLQEvent {
  id: string;
  uuid: string;
  original_topic: string;
  action: string;
  payload: Record<string, unknown>;
  failed_at: string;
  failure_reason: string;
  retry_count: number;
  source: string;
}

const FAILURE_COLORS: Record<string, string> = {
  timeout: "text-edge-orange border-edge-orange/30 bg-edge-orange/10",
  max_retries_exceeded: "text-edge-red border-edge-red/30 bg-edge-red/10",
  invalid_payload: "text-edge-yellow border-edge-yellow/30 bg-edge-yellow/10",
  worker_unavailable: "text-red-400 border-red-400/30 bg-red-400/10",
  circuit_breaker_open: "text-purple-400 border-purple-400/30 bg-purple-400/10",
};

export default function DeadLetterPage() {
  const [events, setEvents] = useState<DLQEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dead-letter").then((r) => r.json()).then((d) => {
      setEvents(d.events);
      setTotal(d.total);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading dead-letter queue...</div>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Dead-Letter Queue</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Failed events beyond max retry</p>
        </div>
        <div className="text-[10px] text-edge-orange uppercase tracking-wider">{total} undelivered</div>
      </div>

      <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
        {events.map((evt) => (
          <div key={evt.id} className="bg-nexus-surface border border-nexus-border rounded-lg p-3 font-mono">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-nexus-muted">{evt.original_topic}</span>
                <span className="text-xs text-nexus-text">{evt.action}</span>
              </div>
              <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${FAILURE_COLORS[evt.failure_reason] || "text-nexus-muted border-nexus-border"}`}>
                {evt.failure_reason}
              </span>
            </div>
            <div className="flex items-center gap-4 text-[10px] text-nexus-muted">
              <span>source: {evt.source}</span>
              <span>retries: {evt.retry_count}</span>
              <span>failed: {new Date(evt.failed_at).toLocaleString()}</span>
              <span className="text-[9px] truncate flex-1" title={evt.uuid}>{evt.uuid}</span>
            </div>
            <pre className="mt-2 text-[9px] text-nexus-muted bg-nexus-bg rounded p-2 overflow-x-auto max-h-20">
              {JSON.stringify(evt.payload, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
