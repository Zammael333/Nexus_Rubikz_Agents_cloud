"use client";

import { useEffect, useState, useCallback } from "react";
import SearchFilter from "@/components/SearchFilter";
import EventDetailModal from "@/components/EventDetailModal";
import CriticalAlertModal from "@/components/CriticalAlertModal";

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

const SEV_COLORS: Record<string, string> = {
  DEBUG: "text-gray-500",
  INFO: "text-blue-400",
  WARN: "text-edge-yellow",
  ERROR: "text-edge-orange",
  CRITICAL: "text-edge-red",
};

const SEV_BG: Record<string, string> = {
  DEBUG: "border-gray-500/30",
  INFO: "border-blue-400/30",
  WARN: "border-edge-yellow/30",
  ERROR: "border-edge-orange/30",
  CRITICAL: "border-edge-red/30",
};

export default function EventsPage() {
  const [events, setEvents] = useState<BusEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<BusEvent | null>(null);
  const [criticalAlert, setCriticalAlert] = useState<{
    event: BusEvent;
    onAck: () => void;
    onEscalate: () => void;
    onDismiss: () => void;
  } | null>(null);

  const fetchEvents = useCallback(async (_query: string, filters: Record<string, string>) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filters.severity && filters.severity !== "ALL") params.set("severity", filters.severity);
    if (filters.worker && filters.worker !== "ALL") params.set("worker", filters.worker);
    if (_query) params.set("q", _query);
    params.set("limit", "100");
    const res = await fetch(`/api/events?${params}`);
    const data = await res.json();
    setEvents(data.events);
    setTotal(data.total);
    setLoading(false);
  }, []);

  useEffect(() => { fetchEvents("", {}); }, [fetchEvents]);

  const showAlert = (evt: BusEvent) => {
    setCriticalAlert({
      event: evt,
      onAck: () => { setCriticalAlert(null); },
      onEscalate: () => { setCriticalAlert(null); },
      onDismiss: () => { setCriticalAlert(null); },
    });
  };

  const filterDefs = [
    { key: "severity", label: "Severity", values: ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"] },
    { key: "worker", label: "Worker", values: Array.from(new Set(events.map((e) => e.worker))).sort() },
  ];

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Event Timeline</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">PubSub bus events — click to inspect</p>
      </div>

      <div className="mb-4">
        <SearchFilter
          placeholder="Search events by action or worker..."
          filters={filterDefs}
          onSearch={fetchEvents}
        />
      </div>

      <div className="text-[10px] text-nexus-muted mb-2 tracking-wider">{total} events</div>

      {loading ? (
        <div className="text-xs text-nexus-muted text-center py-12">Loading events...</div>
      ) : (
        <div className="space-y-1 max-h-[65vh] overflow-y-auto pr-1">
          {events.map((evt) => (
            <div
              key={evt.id}
              onClick={() => {
                if (evt.severity === "CRITICAL") {
                  showAlert(evt);
                } else {
                  setSelectedEvent(evt);
                }
              }}
              className={`flex items-start gap-3 p-2 bg-nexus-surface border-l-2 ${SEV_BG[evt.severity]} rounded text-xs font-mono hover:bg-nexus-border/30 transition-colors ${evt.severity === "CRITICAL" ? "cursor-pointer border-edge-red/60" : "cursor-pointer"}`}
            >
              <div className="w-14 shrink-0">
                <span className={`text-[10px] font-bold uppercase ${SEV_COLORS[evt.severity]}`}>{evt.severity}</span>
              </div>
              <div className="w-20 shrink-0 text-nexus-muted text-[10px]">{new Date(evt.timestamp).toLocaleTimeString()}</div>
              <div className="w-24 shrink-0 text-nexus-text">{evt.worker}</div>
              <div className="flex-1 text-nexus-text">{evt.action}</div>
              <div className="w-28 text-[9px] text-nexus-muted truncate" title={evt.uuid}>{evt.uuid.slice(0, 23)}...</div>
              {evt.trace_id && <div className="w-4 shrink-0" title={`trace: ${evt.trace_id}`}>🔗</div>}
            </div>
          ))}
        </div>
      )}

      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
      <CriticalAlertModal alert={criticalAlert} onClose={() => setCriticalAlert(null)} />
    </div>
  );
}
