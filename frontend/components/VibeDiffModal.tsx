"use client";

import Modal from "@/components/Modal";

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

interface VibeDiffModalProps {
  diff: VibeDiff | null;
  onApprove: (diffId: string) => void;
  onReject: (diffId: string) => void;
  onClose: () => void;
}

export default function VibeDiffModal({ diff, onApprove, onReject, onClose }: VibeDiffModalProps) {
  if (!diff) return null;

  return (
    <Modal open={!!diff} onClose={onClose} title="Review Drift Change" width="w-[32rem]">
      <div className="space-y-3 font-mono">
        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Worker</div>
          <div className="text-xs text-nexus-text">{diff.worker}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Proposed Change</div>
          <div className="text-sm text-nexus-text bg-nexus-bg border border-nexus-border rounded p-2">{diff.proposed_change}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Reason</div>
          <div className="text-xs text-nexus-text">{diff.reason}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Drift Impact</div>
          <div className="text-xs text-nexus-text">{diff.drift_impact}</div>
        </div>

        <div className="flex items-center gap-4 text-[10px] text-nexus-muted">
          <span>by: {diff.submitted_by}</span>
          <span>{new Date(diff.submitted_at).toLocaleString()}</span>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            onClick={() => onApprove(diff.id)}
            className="flex-1 px-3 py-1.5 bg-edge-green/20 text-edge-green text-[10px] uppercase tracking-wider border border-edge-green/30 rounded hover:bg-edge-green/30 transition-colors"
          >
            Approve
          </button>
          <button
            onClick={() => onReject(diff.id)}
            className="flex-1 px-3 py-1.5 bg-edge-red/20 text-edge-red text-[10px] uppercase tracking-wider border border-edge-red/30 rounded hover:bg-edge-red/30 transition-colors"
          >
            Reject
          </button>
        </div>
      </div>
    </Modal>
  );
}
