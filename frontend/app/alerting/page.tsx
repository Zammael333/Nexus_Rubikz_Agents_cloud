"use client";

import { useEffect, useState } from "react";
import type { AlertRule } from "@/app/api/alerting/route";

export default function AlertingPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/alerting").then((r) => r.json()).then((d) => { setRules(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading alerting rules...</div>;
  if (!rules.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No alerting rules</div>;

  const severityColor = (s: string) => s === "critical" ? "text-edge-orange" : s === "warning" ? "text-edge-yellow" : "text-nexus-muted";
  const activeCount = rules.filter((r) => r.enabled).length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Alerting Rules</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Alert rule configuration & status</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-nexus-muted">{activeCount}/{rules.length} active</span>
          <span className="text-[10px] text-edge-green px-2 py-1 rounded bg-edge-green/10 border border-edge-green/30">{rules.filter((r) => r.last_fired).length} recently fired</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left py-2 pr-2">Rule</th>
              <th className="text-left py-2 pr-2">Metric</th>
              <th className="text-left py-2 pr-2">Condition</th>
              <th className="text-left py-2 pr-2">Severity</th>
              <th className="text-left py-2 pr-2">Interval</th>
              <th className="text-left py-2 pr-2">Status</th>
              <th className="text-left py-2 pr-2">Last Fired</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className="border-b border-nexus-border/50 hover:bg-nexus-border/20 transition-colors">
                <td className="py-2 pr-2 text-nexus-text font-mono">{rule.name}</td>
                <td className="py-2 pr-2 text-nexus-muted">{rule.metric}</td>
                <td className="py-2 pr-2 text-nexus-text font-mono">{rule.condition} {rule.threshold}</td>
                <td className={`py-2 pr-2 font-mono ${severityColor(rule.severity)}`}>{rule.severity}</td>
                <td className="py-2 pr-2 text-nexus-muted">{rule.interval}</td>
                <td className="py-2 pr-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] ${rule.enabled ? "bg-edge-green/10 text-edge-green border border-edge-green/30" : "bg-nexus-border/30 text-nexus-muted border border-nexus-border"}`}>
                    {rule.enabled ? "enabled" : "disabled"}
                  </span>
                </td>
                <td className="py-2 pr-2 text-nexus-muted font-mono text-[10px]">{rule.last_fired ? new Date(rule.last_fired).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
