"use client";

import type { ReactNode } from "react";

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

interface CriticalAlert {
  event: BusEvent;
  onAck: () => void;
  onEscalate: () => void;
  onDismiss: () => void;
}

interface CriticalAlertModalProps {
  alert: CriticalAlert | null;
  onClose: () => void;
}

export default function CriticalAlertModal({ alert, onClose }: CriticalAlertModalProps) {
  if (!alert) return null;
  const { event, onAck, onEscalate, onDismiss } = alert;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60]" onClick={onClose}>
      <div
        className="bg-nexus-surface border border-edge-red/30 rounded-lg p-6 w-96 animate-pulse-border"
        onClick={(e) => e.stopPropagation()}
      >
        <style>{`
          @keyframes pulseBorder {
            0%, 100% { border-color: rgba(255,0,51,0.3); }
            50% { border-color: rgba(255,0,51,0.7); }
          }
          .animate-pulse-border {
            animation: pulseBorder 2s ease-in-out infinite;
          }
        `}</style>

        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border bg-edge-red/20 text-edge-red border-edge-red/30">
            CRITICAL
          </span>
          <button
            onClick={onClose}
            className="text-nexus-muted hover:text-nexus-text text-xs transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3 font-mono">
          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Alert</div>
            <div className="text-sm font-bold text-edge-red uppercase tracking-wider">{event.action}</div>
          </div>

          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Worker</div>
            <div className="text-xs text-nexus-text">{event.worker}</div>
          </div>

          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Timestamp</div>
            <div className="text-xs text-nexus-text">{event.timestamp}</div>
          </div>

          <div>
            <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Payload Summary</div>
            <pre className="text-[10px] text-nexus-text bg-nexus-bg border border-nexus-border rounded p-2 overflow-x-auto whitespace-pre-wrap max-h-28">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          </div>

          {event.trace_id && (
            <div>
              <div className="text-[10px] text-nexus-muted uppercase tracking-wider mb-1">Trace ID</div>
              <div className="text-xs text-nexus-text break-all">{event.trace_id}</div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button
              onClick={onAck}
              className="flex-1 px-3 py-1.5 bg-edge-green/20 text-edge-green text-[10px] uppercase tracking-wider border border-edge-green/30 rounded hover:bg-edge-green/30 transition-colors"
            >
              ACK
            </button>
            <button
              onClick={onEscalate}
              className="flex-1 px-3 py-1.5 bg-edge-orange/20 text-edge-orange text-[10px] uppercase tracking-wider border border-edge-orange/30 rounded hover:bg-edge-orange/30 transition-colors"
            >
              ESCALATE
            </button>
            <button
              onClick={onDismiss}
              className="flex-1 px-3 py-1.5 text-nexus-muted text-[10px] uppercase tracking-wider border border-nexus-border rounded hover:text-nexus-text transition-colors"
            >
              DISMISS
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
