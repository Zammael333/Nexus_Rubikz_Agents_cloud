"use client";

import { useEffect, useState } from "react";

interface Span {
  span_id: string;
  name: string;
  parent_id: string | null;
  duration_ms: number;
  start_time: string;
  status: string;
}

interface Trace {
  trace_id: string;
  spans: Span[];
}

function WaterfallSpan({ span, maxDuration, depth }: { span: Span; maxDuration: number; depth: number }) {
  const widthPct = (span.duration_ms / maxDuration) * 100;
  const isError = span.status === "error";
  return (
    <div className="flex items-center gap-2 py-1" style={{ paddingLeft: `${depth * 20 + 8}px` }}>
      <div className="flex-1 relative h-5 bg-nexus-bg rounded overflow-hidden">
        <div
          className={`absolute top-0 h-full rounded ${isError ? "bg-edge-red/40 border border-edge-red/60" : "bg-edge-green/20 border border-edge-green/30"}`}
          style={{ width: `${Math.max(widthPct, 2)}%` }}
        />
      </div>
      <div className="w-12 text-right text-[10px] text-nexus-text font-mono">{span.duration_ms}ms</div>
      <div className="w-32 text-[10px] text-nexus-muted truncate">{span.name}</div>
      {isError && <span className="text-[8px] text-edge-red uppercase tracking-wider">error</span>}
    </div>
  );
}

export default function TracesPage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["trace-001"]));

  useEffect(() => {
    fetch("/api/traces").then((r) => r.json()).then((d) => { setTraces(d.traces); setLoading(false); });
  }, []);

  const toggleTrace = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  function getRoot(spans: Span[]): Span {
    return spans.find((s) => s.parent_id === null) || spans[0];
  }

  function childrenOf(spans: Span[], parentId: string): Span[] {
    return spans.filter((s) => s.parent_id === parentId);
  }

  function renderSpanTree(spans: Span[], parentId: string | null, depth: number, maxDuration: number): JSX.Element[] {
    return spans
      .filter((s) => s.parent_id === parentId)
      .flatMap((span) => [
        <WaterfallSpan key={span.span_id} span={span} maxDuration={maxDuration} depth={depth} />,
        ...renderSpanTree(spans, span.span_id, depth + 1, maxDuration),
      ]);
  }

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading traces...</div>;

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Einstein-Williams Traces</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">OTEL span waterfall graph</p>
      </div>

      <div className="space-y-3">
        {traces.map((trace) => {
          const root = getRoot(trace.spans);
          const maxDur = Math.max(...trace.spans.map((s) => s.duration_ms));
          const isOpen = expanded.has(trace.trace_id);
          const hasError = trace.spans.some((s) => s.status === "error");

          return (
            <div key={trace.trace_id} className="bg-nexus-surface border border-nexus-border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleTrace(trace.trace_id)}
                className="w-full flex items-center justify-between p-3 hover:bg-nexus-bg/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs text-nexus-muted">{isOpen ? "▼" : "▶"}</span>
                  <span className="text-xs font-bold text-nexus-text font-mono">{trace.trace_id}</span>
                  <span className="text-[10px] text-nexus-muted">{root.name}</span>
                  {hasError && <span className="text-[9px] text-edge-red uppercase tracking-wider px-1.5 py-0.5 rounded bg-edge-red/10 border border-edge-red/30">has error</span>}
                </div>
                <span className="text-[10px] text-nexus-muted font-mono">{root.duration_ms}ms</span>
              </button>

              {isOpen && (
                <div className="px-3 pb-3">
                  <div className="flex items-center text-[9px] text-nexus-muted uppercase tracking-wider mb-1 px-1">
                    <span className="flex-1">Timeline</span>
                    <span className="w-12 text-right">Duration</span>
                    <span className="w-32 text-right">Span</span>
                  </div>
                  {renderSpanTree(trace.spans, null, 0, maxDur)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
