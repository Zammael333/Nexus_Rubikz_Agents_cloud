"use client";

import { useEffect, useState } from "react";
import { EdgeGlowDot, type Pulse } from "@/components/EdgeGlow";

interface SPIFFEIdentity {
  id: string;
  spiffe_id: string;
  worker: string;
  status: string;
  issued_at: string;
  expires_at: string;
  ttl_hours: number;
  last_used: string;
}

const STATUS_STYLES: Record<string, { pulse: Pulse; color: string }> = {
  valid: { pulse: "green", color: "text-edge-green border-edge-green/30 bg-edge-green/10" },
  expiring: { pulse: "yellow", color: "text-edge-yellow border-edge-yellow/30 bg-edge-yellow/10" },
  revoked: { pulse: "red", color: "text-edge-red border-edge-red/30 bg-edge-red/10" },
};

export default function SPIFFEPage() {
  const [identities, setIdentities] = useState<SPIFFEIdentity[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/spiffe").then((r) => r.json()).then((d) => {
      setIdentities(d.identities);
      setTotal(d.total);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading SPIFFE identities...</div>;

  const valid = identities.filter((i) => i.status === "valid").length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">SPIFFE Identities</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">mTLS worker certificates and trust domains</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-nexus-muted uppercase tracking-wider">{valid}/{total} valid</span>
          <EdgeGlowDot pulse="green" size="sm" />
        </div>
      </div>

      <div className="border border-nexus-border rounded-lg overflow-hidden">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="bg-nexus-surface border-b border-nexus-border">
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">SPIFFE ID</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Worker</th>
              <th className="text-center p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Status</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Issued</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Expires</th>
              <th className="text-right p-3 text-nexus-muted text-[10px] uppercase tracking-wider">TTL (h)</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Last Used</th>
            </tr>
          </thead>
          <tbody>
            {identities.map((id) => {
              const style = STATUS_STYLES[id.status] || { pulse: "green" as Pulse, color: "text-nexus-muted border-nexus-border" };
              return (
                <tr key={id.id} className="border-b border-nexus-border/50 hover:bg-nexus-surface/50 transition-colors">
                  <td className="p-3 text-edge-green text-[10px]">{id.spiffe_id}</td>
                  <td className="p-3 text-nexus-text">{id.worker}</td>
                  <td className="p-3 text-center">
                    <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border inline-flex items-center gap-1.5 ${style.color}`}>
                      <EdgeGlowDot pulse={style.pulse} size="sm" />
                      {id.status}
                    </span>
                  </td>
                  <td className="p-3 text-nexus-muted text-[10px]">{new Date(id.issued_at).toLocaleDateString()}</td>
                  <td className="p-3 text-nexus-muted text-[10px]">{new Date(id.expires_at).toLocaleDateString()}</td>
                  <td className="p-3 text-right text-nexus-text">{id.ttl_hours}</td>
                  <td className="p-3 text-nexus-muted text-[10px]">{new Date(id.last_used).toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
