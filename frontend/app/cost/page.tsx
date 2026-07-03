"use client";

import { useEffect, useState } from "react";
import type { CostEntry } from "@/app/api/cost/route";

export default function CostPage() {
  const [costs, setCosts] = useState<CostEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/cost").then((r) => r.json()).then((d) => { setCosts(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading cost data...</div>;
  if (!costs.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No cost data</div>;

  const total = costs.reduce((a, c) => a + c.monthly_cost, 0);
  const totalBudget = costs.reduce((a, c) => a + c.budget, 0);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Cost Explorer</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Cloud cost breakdown & budgets</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-nexus-muted">${total.toLocaleString()} / month</span>
          <span className="text-[10px] text-edge-green px-2 py-1 rounded bg-edge-green/10 border border-edge-green/30">
            {Math.round((total / totalBudget) * 100)}% of budget
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {costs.map((c) => {
          const pct = Math.round((c.monthly_cost / c.budget) * 100);
          const barColor = pct > 90 ? "bg-edge-orange" : pct > 75 ? "bg-edge-yellow" : "bg-edge-green";
          return (
            <div key={c.id} className="bg-nexus-surface border border-nexus-border rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-nexus-text">{c.service}</span>
                <span className="text-[10px] text-nexus-muted">{c.category}</span>
              </div>
              <div className="text-sm font-bold text-nexus-text font-mono mb-1">${c.monthly_cost.toLocaleString()}</div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-[10px] ${c.trend_pct >= 0 ? "text-edge-orange" : "text-edge-green"}`}>
                  {c.trend_pct >= 0 ? "↑" : "↓"} {Math.abs(c.trend_pct)}%
                </span>
                <span className="text-[10px] text-nexus-muted">budget ${c.budget.toLocaleString()}</span>
              </div>
              <div className="w-full h-1.5 bg-nexus-bg rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.min(pct, 100)}%` }} />
              </div>
              <div className="mt-2 space-y-1">
                {c.projects.map((p) => (
                  <div key={p.name} className="flex justify-between text-[10px]">
                    <span className="text-nexus-muted">{p.name}</span>
                    <span className="text-nexus-text font-mono">${p.cost.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
