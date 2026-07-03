"use client";

import { useEffect, useState } from "react";
import type { Runbook } from "@/app/api/runbooks/route";

export default function RunbooksPage() {
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/runbooks").then((r) => r.json()).then((d) => { setRunbooks(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading runbooks...</div>;
  if (!runbooks.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No runbooks</div>;

  const categories = Array.from(new Set(runbooks.map((r) => r.category)));

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Runbooks</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Operational runbooks & procedures</p>
        </div>
        <div className="flex items-center gap-2">
          {categories.map((cat) => (
            <span key={cat} className="text-[10px] px-2 py-1 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{cat}</span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {runbooks.map((rb) => (
          <div key={rb.id} className="bg-nexus-surface border border-nexus-border rounded-lg p-3 hover:bg-nexus-border/10 transition-colors">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-nexus-text">{rb.title}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{rb.category}</span>
            </div>
            <p className="text-[10px] text-nexus-muted mb-2">{rb.description}</p>
            <div className="flex items-center gap-3 text-[10px] text-nexus-muted">
              <span>{rb.steps} steps</span>
              <span>~{rb.avg_duration_min} min</span>
              <span>Owner: {rb.owner}</span>
              <span>Reviewed: {rb.last_reviewed}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
