export interface MaintenanceWindow {
  id: string;
  title: string;
  scope: string;
  status: "scheduled" | "active" | "completed" | "cancelled";
  scheduled_start: string;
  scheduled_end: string;
  actual_start: string | null;
  actual_end: string | null;
  owner: string;
  impact: string;
}

const windows: MaintenanceWindow[] = [
  { id: "mt-001", title: "Database index rebuild", scope: "PostgreSQL primary (prod)", status: "scheduled", scheduled_start: "2026-07-01T02:00:00Z", scheduled_end: "2026-07-01T04:00:00Z", actual_start: null, actual_end: null, owner: "dba@nexus.io", impact: "Write operations paused ~10min" },
  { id: "mt-002", title: "Kubernetes node upgrade", scope: "gke-nodes (prod pool)", status: "scheduled", scheduled_start: "2026-07-02T03:00:00Z", scheduled_end: "2026-07-02T05:00:00Z", actual_start: null, actual_end: null, owner: "sre@nexus.io", impact: "Pods drained with PDB, zero downtime" },
  { id: "mt-003", title: "SPIFFE SPIRE refresh", scope: "SPIRE server", status: "active", scheduled_start: "2026-06-30T22:00:00Z", scheduled_end: "2026-06-30T23:00:00Z", actual_start: "2026-06-30T22:05:00Z", actual_end: null, owner: "security@nexus.io", impact: "SVID issuance delayed ~15s" },
  { id: "mt-004", title: "Certificate rotation", scope: "Wildcard *.nexus.io TLS", status: "completed", scheduled_start: "2026-06-29T02:00:00Z", scheduled_end: "2026-06-29T03:00:00Z", actual_start: "2026-06-29T02:00:00Z", actual_end: "2026-06-29T02:15:00Z", owner: "security@nexus.io", impact: "None (zero-downtime rotation)" },
  { id: "mt-005", title: "Storage tier migration", scope: "GCS coldline → archive", status: "completed", scheduled_start: "2026-06-28T03:00:00Z", scheduled_end: "2026-06-28T06:00:00Z", actual_start: "2026-06-28T03:00:00Z", actual_end: "2026-06-28T05:30:00Z", owner: "ops@nexus.io", impact: "Archive data read-only during migration" },
  { id: "mt-006", title: "Network ACL audit", scope: "VPC firewall rules", status: "completed", scheduled_start: "2026-06-27T04:00:00Z", scheduled_end: "2026-06-27T06:00:00Z", actual_start: "2026-06-27T04:00:00Z", actual_end: "2026-06-27T04:45:00Z", owner: "security@nexus.io", impact: "None (read-only audit)" },
  { id: "mt-007", title: "Load test preparation", scope: "Staging cluster", status: "scheduled", scheduled_start: "2026-07-03T10:00:00Z", scheduled_end: "2026-07-03T14:00:00Z", actual_start: null, actual_end: null, owner: "perf@nexus.io", impact: "Staging unavailable during test" },
  { id: "mt-008", title: "Phoenix protocol dry-run", scope: "Worker-3 recovery", status: "completed", scheduled_start: "2026-06-26T22:00:00Z", scheduled_end: "2026-06-26T23:00:00Z", actual_start: "2026-06-26T22:00:00Z", actual_end: "2026-06-26T22:30:00Z", owner: "sre@nexus.io", impact: "Worker-3 offline for 30 min" },
];

export async function GET() {
  return Response.json(windows);
}
