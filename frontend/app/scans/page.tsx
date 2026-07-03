"use client";

import { useEffect, useState } from "react";

interface Scan {
  id: string;
  started_at: string;
  duration_sec: number;
  items_scanned: number;
  dead_stock_found: number;
  anomalies: number;
  status: "completed" | "failed";
}

function formatDuration(sec: number): string {
  const min = Math.floor(sec / 60);
  const s = sec % 60;
  return min > 0 ? `${min}m ${s}s` : `${s}s`;
}

export default function ScansPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/scans").then((r) => r.json()).then((d) => { setScans(d.scans); setLoading(false); });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading scan history...</div>;

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Scorpion Scans</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Historical inventory scan results</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[9px] text-nexus-muted uppercase tracking-wider border-b border-nexus-border">
              <th className="text-left p-2">Scan ID</th>
              <th className="text-left p-2">Date</th>
              <th className="text-right p-2">Duration</th>
              <th className="text-right p-2">Items</th>
              <th className="text-right p-2">Dead Stock</th>
              <th className="text-right p-2">Anomalies</th>
              <th className="text-center p-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((scan) => (
              <tr key={scan.id} className="border-b border-nexus-border/50 hover:bg-nexus-bg/50 transition-colors">
                <td className="p-2 text-nexus-text font-mono">{scan.id}</td>
                <td className="p-2 text-nexus-muted">{new Date(scan.started_at).toLocaleDateString()} {new Date(scan.started_at).toLocaleTimeString()}</td>
                <td className="p-2 text-nexus-text text-right">{formatDuration(scan.duration_sec)}</td>
                <td className="p-2 text-nexus-text text-right">{scan.items_scanned.toLocaleString()}</td>
                <td className="p-2 text-edge-orange text-right">{scan.dead_stock_found}</td>
                <td className="p-2 text-edge-yellow text-right">{scan.anomalies}</td>
                <td className="p-2 text-center">
                  <span className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    scan.status === "completed"
                      ? "bg-edge-green/20 text-edge-green"
                      : "bg-edge-red/20 text-edge-red"
                  }`}>
                    {scan.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
