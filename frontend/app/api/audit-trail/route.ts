export interface AuditEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  detail: string;
  ip_address: string;
}

const entries: AuditEntry[] = [
  { id: "ae-001", timestamp: "2026-06-30T14:30:00Z", actor: "admin@nexus.io", action: "config.update", resource: "slo_target", detail: "Updated SLO target from 99.99% to 99.997%", ip_address: "10.0.1.20" },
  { id: "ae-002", timestamp: "2026-06-30T13:15:00Z", actor: "operator@nexus.io", action: "deploy.rollback", resource: "worker:watchdog", detail: "Rolled back watchdog v2.4.1 → v2.4.0", ip_address: "10.0.1.21" },
  { id: "ae-003", timestamp: "2026-06-30T12:00:00Z", actor: "ci-bot@nexus.io", action: "deploy.progress", resource: "worker:notifier", detail: "Deployed notifier v1.8.3 to staging", ip_address: "10.0.1.5" },
  { id: "ae-004", timestamp: "2026-06-30T10:45:00Z", actor: "admin@nexus.io", action: "secret.rotate", resource: "spiffe:worker-3", detail: "Rotated SPIFFE SVID for worker-3", ip_address: "10.0.1.20" },
  { id: "ae-005", timestamp: "2026-06-30T09:30:00Z", actor: "system", action: "alert.fired", resource: "rule:cpu-90", detail: "Alert 'CPU > 90%' fired for worker-1", ip_address: "127.0.0.1" },
  { id: "ae-006", timestamp: "2026-06-30T08:00:00Z", actor: "operator@nexus.io", action: "config.create", resource: "alert_rule", detail: "Created alert rule 'Disk > 80%'", ip_address: "10.0.1.21" },
  { id: "ae-007", timestamp: "2026-06-29T23:00:00Z", actor: "system", action: "backup.completed", resource: "config_db", detail: "Daily config backup completed (1.2 GB)", ip_address: "127.0.0.1" },
  { id: "ae-008", timestamp: "2026-06-29T22:00:00Z", actor: "admin@nexus.io", action: "user.role_update", resource: "user:jdoe", detail: "Changed jdoe role from viewer to operator", ip_address: "10.0.1.20" },
  { id: "ae-009", timestamp: "2026-06-29T21:00:00Z", actor: "operator@nexus.io", action: "maintenance.start", resource: "cluster:prod", detail: "Started maintenance window for prod cluster", ip_address: "10.0.1.21" },
  { id: "ae-010", timestamp: "2026-06-29T20:00:00Z", actor: "ci-bot@nexus.io", action: "scan.completed", resource: "scorpion:full", detail: "Full Scorpion scan completed (0 anomalies found)", ip_address: "10.0.1.5" },
  { id: "ae-011", timestamp: "2026-06-29T18:00:00Z", actor: "admin@nexus.io", action: "permission.grant", resource: "api:export", detail: "Granted API export permission to service-account-4", ip_address: "10.0.1.20" },
  { id: "ae-012", timestamp: "2026-06-29T16:00:00Z", actor: "system", action: "cert.renewed", resource: "tls:*.nexus.io", detail: "Auto-renewed wildcard certificate (expires 2027-06-29)", ip_address: "127.0.0.1" },
  { id: "ae-013", timestamp: "2026-06-29T14:00:00Z", actor: "operator@nexus.io", action: "incident.acknowledge", resource: "inc-042", detail: "Acknowledged incident INC-042", ip_address: "10.0.1.21" },
  { id: "ae-014", timestamp: "2026-06-29T12:00:00Z", actor: "admin@nexus.io", action: "config.delete", resource: "alert_rule:old-cpu", detail: "Deleted deprecated alert rule 'Old CPU Check'", ip_address: "10.0.1.20" },
  { id: "ae-015", timestamp: "2026-06-29T10:00:00Z", actor: "system", action: "backup.verified", resource: "config_db", detail: "Backup integrity check passed (SHA-256 verified)", ip_address: "127.0.0.1" },
];

export async function GET() {
  return Response.json(entries);
}
