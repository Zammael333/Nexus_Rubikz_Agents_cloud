"use client";

import { useState } from "react";

interface PhoenixControlProps {
  workerId: string;
  workerLabel: string;
  onRestart: (workerId: string) => Promise<void>;
}

export default function PhoenixControl({ workerId, workerLabel, onRestart }: PhoenixControlProps) {
  const [confirming, setConfirming] = useState(false);
  const [restarting, setRestarting] = useState(false);

  const handleRestart = async () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setRestarting(true);
    try {
      await onRestart(workerId);
    } finally {
      setRestarting(false);
      setConfirming(false);
    }
  };

  return (
    <div className="mt-2 pt-2 border-t border-nexus-border">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-nexus-muted uppercase tracking-wider">Phoenix</span>
        <span className="text-[10px] text-edge-green font-semibold">RTO ~1800ms</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-edge-green shadow-[0_0_6px_rgba(0,255,136,0.5)]" />
          <span className="text-[10px] text-nexus-text">active</span>
        </div>
        <button
          onClick={handleRestart}
          disabled={restarting}
          className={`ml-auto text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-colors ${
            confirming
              ? "bg-edge-orange/20 text-edge-orange border-edge-orange/30"
              : "border-nexus-border text-nexus-muted hover:text-nexus-text"
          } disabled:opacity-50`}
        >
          {restarting ? "..." : confirming ? "Confirm?" : "Restart Worker"}
        </button>
      </div>
      {confirming && (
        <button
          onClick={() => setConfirming(false)}
          className="text-[9px] text-nexus-muted hover:text-nexus-text mt-1"
        >
          Cancel
        </button>
      )}
    </div>
  );
}
