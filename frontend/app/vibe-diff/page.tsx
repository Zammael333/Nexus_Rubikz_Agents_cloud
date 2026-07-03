"use client";

import { useEffect, useState } from "react";
import VibeDiffModal from "@/components/VibeDiffModal";

interface VibeDiff {
  id: string;
  worker: string;
  proposed_change: string;
  reason: string;
  drift_impact: string;
  submitted_at: string;
  status: "pending" | "approved" | "rejected";
  submitted_by: string;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "text-edge-yellow border-edge-yellow/30 bg-edge-yellow/10",
  approved: "text-edge-green border-edge-green/30 bg-edge-green/10",
  rejected: "text-edge-red border-edge-red/30 bg-edge-red/10",
};

export default function VibeDiffPage() {
  const [diffs, setDiffs] = useState<VibeDiff[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<VibeDiff | null>(null);

  const fetchDiffs = () => fetch("/api/vibe-diff").then((r) => r.json()).then((d) => { setDiffs(d.diffs); setLoading(false); });

  useEffect(() => { fetchDiffs(); }, []);

  const handleDecision = async (diffId: string, decision: "approved" | "rejected") => {
    setDiffs((prev) => prev.map((d) => d.id === diffId ? { ...d, status: decision } : d));
    setSelected(null);
  };

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading vibe diffs...</div>;

  const pending = diffs.filter((d) => d.status === "pending").length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Vibe Diff</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Drift-change proposals requiring approval</p>
        </div>
        {pending > 0 && (
          <div className="text-[10px] text-edge-yellow uppercase tracking-wider">{pending} pending review</div>
        )}
      </div>

      <div className="space-y-2">
        {diffs.map((diff) => (
          <div
            key={diff.id}
            onClick={() => diff.status === "pending" && setSelected(diff)}
            className={`bg-nexus-surface border border-nexus-border rounded-lg p-4 ${diff.status === "pending" ? "cursor-pointer hover:border-edge-yellow/50" : ""} transition-colors`}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-xs font-bold text-nexus-text uppercase tracking-wider">{diff.worker}</span>
                <span className="text-[10px] text-nexus-muted ml-2">{diff.id}</span>
              </div>
              <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${STATUS_STYLES[diff.status]}`}>
                {diff.status}
              </span>
            </div>
            <p className="text-xs text-nexus-text mb-2">{diff.proposed_change}</p>
            <div className="flex items-center gap-4 text-[10px] text-nexus-muted">
              <span>by: {diff.submitted_by}</span>
              <span>impact: {diff.drift_impact}</span>
              <span>{new Date(diff.submitted_at).toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      <VibeDiffModal
        diff={selected}
        onApprove={(id) => handleDecision(id, "approved")}
        onReject={(id) => handleDecision(id, "rejected")}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
