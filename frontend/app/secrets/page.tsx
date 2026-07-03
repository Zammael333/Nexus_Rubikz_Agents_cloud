"use client";

import { useEffect, useState } from "react";
import type { SecretEntry } from "@/app/api/secrets/route";

export default function SecretsPage() {
  const [secrets, setSecrets] = useState<SecretEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/secrets").then((r) => r.json()).then((d) => { setSecrets(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading secrets...</div>;
  if (!secrets.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No secrets</div>;

  const statusColor = (s: string) => s === "active" ? "text-edge-green" : s === "expiring" ? "text-edge-yellow" : s === "expired" ? "text-edge-orange" : "text-blue-400";

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Secrets Management</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Secret rotation & lifecycle tracking</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-edge-yellow px-2 py-1 rounded bg-edge-yellow/10 border border-edge-yellow/30">{secrets.filter((s) => s.status === "expiring").length} expiring</span>
          <span className="text-[10px] text-edge-orange px-2 py-1 rounded bg-edge-orange/10 border border-edge-orange/30">{secrets.filter((s) => s.status === "expired").length} expired</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left py-2 pr-2">Secret</th>
              <th className="text-left py-2 pr-2">Type</th>
              <th className="text-left py-2 pr-2">Status</th>
              <th className="text-left py-2 pr-2">Version</th>
              <th className="text-left py-2 pr-2">Last Rotated</th>
              <th className="text-left py-2 pr-2">Next Rotation</th>
              <th className="text-left py-2 pr-2">Created By</th>
            </tr>
          </thead>
          <tbody>
            {secrets.map((sec) => (
              <tr key={sec.id} className="border-b border-nexus-border/50 hover:bg-nexus-border/20 transition-colors">
                <td className="py-2 pr-2 text-nexus-text font-mono">{sec.name}</td>
                <td className="py-2 pr-2">
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{sec.type}</span>
                </td>
                <td className={`py-2 pr-2 font-mono ${statusColor(sec.status)}`}>{sec.status}</td>
                <td className="py-2 pr-2 text-nexus-muted font-mono">v{sec.version}</td>
                <td className="py-2 pr-2 text-nexus-muted font-mono text-[10px]">{sec.last_rotated}</td>
                <td className="py-2 pr-2 text-nexus-muted font-mono text-[10px]">{sec.next_rotation}</td>
                <td className="py-2 pr-2 text-nexus-muted text-[10px]">{sec.created_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
