export interface BackupEntry {
  id: string;
  name: string;
  type: "full" | "incremental" | "snapshot";
  size_bytes: number;
  status: "completed" | "running" | "failed";
  started_at: string;
  completed_at: string | null;
  location: string;
  checksum: string;
}

const backups: BackupEntry[] = [
  { id: "bk-001", name: "prod-config-daily", type: "full", size_bytes: 1280000000, status: "completed", started_at: "2026-06-30T23:00:00Z", completed_at: "2026-06-30T23:12:00Z", location: "gs://nexus-backups/config/", checksum: "sha256:a1b2c3d4e5f6..." },
  { id: "bk-002", name: "worker-state-hourly", type: "incremental", size_bytes: 256000000, status: "completed", started_at: "2026-06-30T22:00:00Z", completed_at: "2026-06-30T22:08:00Z", location: "gs://nexus-backups/state/", checksum: "sha256:b2c3d4e5f6a7..." },
  { id: "bk-003", name: "spiffe-db-snapshot", type: "snapshot", size_bytes: 512000000, status: "completed", started_at: "2026-06-30T21:00:00Z", completed_at: "2026-06-30T21:05:00Z", location: "gs://nexus-backups/spiffe/", checksum: "sha256:c3d4e5f6a7b8..." },
  { id: "bk-004", name: "prod-config-daily", type: "full", size_bytes: 1275000000, status: "failed", started_at: "2026-06-29T23:00:00Z", completed_at: "2026-06-29T23:03:00Z", location: "gs://nexus-backups/config/", checksum: "sha256:d4e5f6a7b8c9..." },
  { id: "bk-005", name: "event-log-weekly", type: "full", size_bytes: 4800000000, status: "running", started_at: "2026-06-29T22:00:00Z", completed_at: null, location: "gs://nexus-backups/events/", checksum: "sha256:e5f6a7b8c9d0..." },
  { id: "bk-006", name: "worker-state-hourly", type: "incremental", size_bytes: 245000000, status: "completed", started_at: "2026-06-29T21:00:00Z", completed_at: "2026-06-29T21:07:00Z", location: "gs://nexus-backups/state/", checksum: "sha256:f6a7b8c9d0e1..." },
  { id: "bk-007", name: "certificates-daily", type: "full", size_bytes: 85000000, status: "completed", started_at: "2026-06-29T20:00:00Z", completed_at: "2026-06-29T20:02:00Z", location: "gs://nexus-backups/certs/", checksum: "sha256:a7b8c9d0e1f2..." },
  { id: "bk-008", name: "slo-metrics-hourly", type: "incremental", size_bytes: 180000000, status: "completed", started_at: "2026-06-29T19:00:00Z", completed_at: "2026-06-29T19:06:00Z", location: "gs://nexus-backups/metrics/", checksum: "sha256:b8c9d0e1f2a3..." },
  { id: "bk-009", name: "prod-config-daily", type: "full", size_bytes: 1270000000, status: "completed", started_at: "2026-06-28T23:00:00Z", completed_at: "2026-06-28T23:11:00Z", location: "gs://nexus-backups/config/", checksum: "sha256:c9d0e1f2a3b4..." },
  { id: "bk-010", name: "audit-log-weekly", type: "full", size_bytes: 3200000000, status: "completed", started_at: "2026-06-28T22:00:00Z", completed_at: "2026-06-28T22:20:00Z", location: "gs://nexus-backups/audit/", checksum: "sha256:d0e1f2a3b4c5..." },
  { id: "bk-011", name: "worker-state-hourly", type: "incremental", size_bytes: 250000000, status: "completed", started_at: "2026-06-28T21:00:00Z", completed_at: "2026-06-28T21:08:00Z", location: "gs://nexus-backups/state/", checksum: "sha256:e1f2a3b4c5d6..." },
  { id: "bk-012", name: "phoenix-recovery-snapshot", type: "snapshot", size_bytes: 890000000, status: "completed", started_at: "2026-06-28T20:00:00Z", completed_at: "2026-06-28T20:04:00Z", location: "gs://nexus-backups/phoenix/", checksum: "sha256:f2a3b4c5d6e7..." },
];

export async function GET() {
  return Response.json(backups);
}
