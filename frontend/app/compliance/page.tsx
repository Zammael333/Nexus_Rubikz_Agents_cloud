"use client";

import { useEffect, useState } from "react";
import type { ComplianceCheck } from "@/app/api/compliance/route";

export default function CompliancePage() {
  const [checks, setChecks] = useState<ComplianceCheck[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/compliance").then((r) => r.json()).then((d) => { setChecks(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading compliance checks...</div>;
  if (!checks.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No compliance data</div>;

  const statusColor = (s: string) => s === "pass" ? "text-edge-green" : s === "fail" ? "text-edge-orange" : s === "warning" ? "text-edge-yellow" : "text-nexus-muted";
  const frameworks = Array.from(new Set(checks.map((c) => c.framework)));
  const passRate = Math.round((checks.filter((c) => c.status === "pass").length / checks.filter((c) => c.status !== "not_applicable").length) * 100);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Compliance</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Security framework compliance checks</p>
        </div>
        <div className="flex items-center gap-2">
          {frameworks.map((f) => (
            <span key={f} className="text-[10px] px-2 py-1 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{f}</span>
          ))}
          <span className="text-[10px] text-edge-green px-2 py-1 rounded bg-edge-green/10 border border-edge-green/30">{passRate}% pass</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left py-2 pr-2">Control</th>
              <th className="text-left py-2 pr-2">Framework</th>
              <th className="text-left py-2 pr-2">Description</th>
              <th className="text-left py-2 pr-2">Status</th>
              <th className="text-left py-2 pr-2">Owner</th>
              <th className="text-left py-2 pr-2">Checked</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((c) => (
              <tr key={c.id} className="border-b border-nexus-border/50 hover:bg-nexus-border/20 transition-colors">
                <td className="py-2 pr-2 text-nexus-text font-mono">{c.control}</td>
                <td className="py-2 pr-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{c.framework}</span>
                </td>
                <td className="py-2 pr-2 text-nexus-text max-w-xs truncate">{c.description}</td>
                <td className={`py-2 pr-2 font-mono ${statusColor(c.status)}`}>{c.status.replace("_", " ")}</td>
                <td className="py-2 pr-2 text-nexus-muted text-[10px]">{c.owner}</td>
                <td className="py-2 pr-2 text-nexus-muted font-mono text-[10px]">{new Date(c.last_checked).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
