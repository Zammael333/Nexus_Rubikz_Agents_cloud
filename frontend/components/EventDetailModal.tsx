"use client";

import { useState } from "react";
import Modal from "@/components/Modal";

interface BusEvent {
  id: string;
  uuid: string;
  timestamp: string;
  severity: string;
  worker: string;
  action: string;
  payload: Record<string, unknown>;
  trace_id?: string;
}

interface EventDetailModalProps {
  event: BusEvent | null;
  onClose: () => void;
}

const SEV_BADGE: Record<string, string> = {
  DEBUG: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  INFO: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  WARN: "bg-edge-yellow/20 text-edge-yellow border-edge-yellow/30",
  ERROR: "bg-edge-orange/20 text-edge-orange border-edge-orange/30",
  CRITICAL: "bg-edge-red/20 text-edge-red border-edge-red/30",
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      onClick={handleCopy}
      className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border border-nexus-border text-nexus-muted hover:text-edge-green hover:border-edge-green/30 transition-colors"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export default function EventDetailModal({ event, onClose }: EventDetailModalProps) {
  if (!event) return null;

  const sevClass = SEV_BADGE[event.severity] || "bg-nexus-surface text-nexus-text border-nexus-border";

  return (
    <Modal open={!!event} onClose={onClose} title="Event Detail">
      <div className="space-y-3 font-mono">
        <div>
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${sevClass}`}>
            {event.severity}
          </span>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">UUID</div>
          <div className="text-xs text-nexus-text break-all">{event.uuid}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Timestamp</div>
          <div className="text-xs text-nexus-text">{event.timestamp}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Worker</div>
          <div className="text-xs text-nexus-text">{event.worker}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Action</div>
          <div className="text-xs text-nexus-text">{event.action}</div>
        </div>

        <div>
          <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Payload</div>
          <pre className="text-[10px] text-nexus-text bg-nexus-bg border border-nexus-border rounded p-2 overflow-x-auto whitespace-pre-wrap max-h-40">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        </div>

        {event.trace_id && (
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">
              Trace ID
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-nexus-text font-mono break-all">{event.trace_id}</span>
              <CopyButton text={event.trace_id} />
            </div>
          </div>
        )}

        {event.trace_id && (
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">
              OTEL Trace Info
            </div>
            <div className="bg-nexus-bg border border-nexus-border rounded p-2 text-[10px] text-nexus-muted">
              trace_id: {event.trace_id}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
