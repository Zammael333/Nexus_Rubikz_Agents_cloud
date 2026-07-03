"use client";

import { useEffect, useState } from "react";
import type { BackupEntry } from "@/app/api/backups/route";

function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  if (bytes >= 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
  return `${bytes} B`;
}

export default function BackupsPage() {
  const [backups, setBackups] = useState<BackupEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/backups").then((r) => r.json()).then((d) => { setBackups(d); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading backups...</div>;
  if (!backups.length) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">No backups found</div>;

  const statusColor = (s: string) => s === "completed" ? "text-edge-green" : s === "running" ? "text-edge-yellow" : "text-edge-orange";
  const lastSuccess = backups.filter((b) => b.status === "completed").length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Backup Status</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Snapshot & backup management</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-nexus-muted">{lastSuccess} successful</span>
          <span className="text-[10px] text-edge-green px-2 py-1 rounded bg-edge-green/10 border border-edge-green/30">Total: {formatBytes(backups.reduce((a, b) => a + b.size_bytes, 0))}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left py-2 pr-2">Name</th>
              <th className="text-left py-2 pr-2">Type</th>
              <th className="text-left py-2 pr-2">Size</th>
              <th className="text-left py-2 pr-2">Status</th>
              <th className="text-left py-2 pr-2">Started</th>
              <th className="text-left py-2 pr-2">Duration</th>
            </tr>
          </thead>
          <tbody>
            {backups.map((bk) => {
              const dur = bk.completed_at
                ? `${Math.round((new Date(bk.completed_at).getTime() - new Date(bk.started_at).getTime()) / 60000)}min`
                : "—";
              return (
                <tr key={bk.id} className="border-b border-nexus-border/50 hover:bg-nexus-border/20 transition-colors">
                  <td className="py-2 pr-2 text-nexus-text font-mono">{bk.name}</td>
                  <td className="py-2 pr-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-nexus-border/30 text-nexus-muted border border-nexus-border">{bk.type}</span>
                  </td>
                  <td className="py-2 pr-2 text-nexus-muted font-mono">{formatBytes(bk.size_bytes)}</td>
                  <td className={`py-2 pr-2 font-mono ${statusColor(bk.status)}`}>{bk.status}</td>
                  <td className="py-2 pr-2 text-nexus-muted font-mono text-[10px]">{new Date(bk.started_at).toLocaleString()}</td>
                  <td className="py-2 pr-2 text-nexus-muted">{dur}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
