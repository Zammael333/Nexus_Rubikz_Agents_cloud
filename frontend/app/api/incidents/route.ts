export interface Incident {
  id: string;
  title: string;
  severity: "SEV1" | "SEV2" | "SEV3";
  status: "open" | "investigating" | "mitigated" | "resolved";
  detected_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  affected_workers: string[];
  summary: string;
}

const incidents: Incident[] = [
  { id: "inc-050", title: "Watchdog CPU spike to 95%", severity: "SEV2", status: "open", detected_at: "2026-06-30T14:30:00Z", acknowledged_at: "2026-06-30T14:32:00Z", resolved_at: null, affected_workers: ["watchdog"], summary: "Unexpected CPU spike on watchdog worker due to backlogged health checks" },
  { id: "inc-049", title: "Notifier downstream timeout", severity: "SEV3", status: "resolved", detected_at: "2026-06-30T10:00:00Z", acknowledged_at: "2026-06-30T10:05:00Z", resolved_at: "2026-06-30T10:30:00Z", affected_workers: ["notifier"], summary: "Third-party webhook endpoint timing out after 30s" },
  { id: "inc-048", title: "Memory leak in Sensor worker", severity: "SEV2", status: "mitigated", detected_at: "2026-06-29T22:00:00Z", acknowledged_at: "2026-06-29T22:15:00Z", resolved_at: null, affected_workers: ["sensor"], summary: "Graceful memory growth in sensor worker, mitigated via restart" },
  { id: "inc-047", title: "SPIFFE SVID expiry cascade", severity: "SEV1", status: "resolved", detected_at: "2026-06-29T16:00:00Z", acknowledged_at: "2026-06-29T16:02:00Z", resolved_at: "2026-06-29T17:30:00Z", affected_workers: ["spire-agent", "worker-1", "worker-2"], summary: "Bulk SVID expiry caused authentication failures across 3 workers" },
  { id: "inc-046", title: "Dead-letter queue backlog", severity: "SEV3", status: "resolved", detected_at: "2026-06-29T08:00:00Z", acknowledged_at: "2026-06-29T08:10:00Z", resolved_at: "2026-06-29T09:00:00Z", affected_workers: ["dead-letter"], summary: "Consumer stalled due to schema mismatch, 15K events queued" },
  { id: "inc-045", title: "Graph database replication lag", severity: "SEV2", status: "resolved", detected_at: "2026-06-28T20:00:00Z", acknowledged_at: "2026-06-28T20:30:00Z", resolved_at: "2026-06-28T22:00:00Z", affected_workers: ["graph"], summary: "Replication lag exceeded 5 minutes due to network partition" },
  { id: "inc-044", title: "Health check false positives", severity: "SEV3", status: "resolved", detected_at: "2026-06-28T14:00:00Z", acknowledged_at: "2026-06-28T14:05:00Z", resolved_at: "2026-06-28T15:00:00Z", affected_workers: ["health"], summary: "Misconfigured threshold causing false alerts on all workers" },
  { id: "inc-043", title: "Cloud Storage egress spike", severity: "SEV3", status: "resolved", detected_at: "2026-06-28T10:00:00Z", acknowledged_at: "2026-06-28T10:20:00Z", resolved_at: "2026-06-28T11:00:00Z", affected_workers: ["storage"], summary: "Unexpected egress cost spike due to misconfigured CDN" },
  { id: "inc-042", title: "Phoenix recovery failure", severity: "SEV1", status: "resolved", detected_at: "2026-06-27T16:00:00Z", acknowledged_at: "2026-06-27T16:05:00Z", resolved_at: "2026-06-27T18:00:00Z", affected_workers: ["phoenix", "watchdog"], summary: "Phoenix protocol failed to recover worker-3 due to corrupted snapshot" },
  { id: "inc-041", title: "Latency degradation on twin sync", severity: "SEV2", status: "resolved", detected_at: "2026-06-27T12:00:00Z", acknowledged_at: "2026-06-27T12:10:00Z", resolved_at: "2026-06-27T13:30:00Z", affected_workers: ["twin"], summary: "Twin synchronization latency increased to 12s due to queue congestion" },
];

export async function GET() {
  return Response.json(incidents);
}
