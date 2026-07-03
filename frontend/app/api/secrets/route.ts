export interface SecretEntry {
  id: string;
  name: string;
  type: string;
  last_rotated: string;
  next_rotation: string;
  status: "active" | "expiring" | "expired" | "rotating";
  version: number;
  created_by: string;
}

const secrets: SecretEntry[] = [
  { id: "sec-001", name: "api-gateway-key", type: "HMAC", last_rotated: "2026-06-01", next_rotation: "2026-09-01", status: "active", version: 4, created_by: "admin@nexus.io" },
  { id: "sec-002", name: "db-primary-password", type: "password", last_rotated: "2026-05-15", next_rotation: "2026-08-15", status: "active", version: 7, created_by: "dba@nexus.io" },
  { id: "sec-003", name: "notifier-webhook-secret", type: "HMAC", last_rotated: "2026-04-01", next_rotation: "2026-07-01", status: "expiring", version: 3, created_by: "ops@nexus.io" },
  { id: "sec-004", name: "spiffe-svid-worker-1", type: "SVID", last_rotated: "2026-06-15", next_rotation: "2026-07-15", status: "active", version: 12, created_by: "system" },
  { id: "sec-005", name: "spiffe-svid-worker-2", type: "SVID", last_rotated: "2026-06-15", next_rotation: "2026-07-15", status: "active", version: 12, created_by: "system" },
  { id: "sec-006", name: "spiffe-svid-worker-3", type: "SVID", last_rotated: "2026-05-20", next_rotation: "2026-06-20", status: "expired", version: 11, created_by: "system" },
  { id: "sec-007", name: "cloud-storage-hmac", type: "HMAC", last_rotated: "2026-03-01", next_rotation: "2026-07-01", status: "expiring", version: 2, created_by: "admin@nexus.io" },
  { id: "sec-008", name: "alertmanager-slack-token", type: "OAuth", last_rotated: "2026-06-10", next_rotation: "2026-09-10", status: "active", version: 5, created_by: "sre@nexus.io" },
  { id: "sec-009", name: "tls-wildcard-nexus", type: "TLS", last_rotated: "2026-06-29", next_rotation: "2027-06-29", status: "rotating", version: 3, created_by: "system" },
  { id: "sec-010", name: "grafana-api-key", type: "API Key", last_rotated: "2026-06-05", next_rotation: "2026-07-05", status: "active", version: 8, created_by: "sre@nexus.io" },
  { id: "sec-011", name: "phoenix-recovery-key", type: "RSA", last_rotated: "2026-04-15", next_rotation: "2026-10-15", status: "active", version: 1, created_by: "admin@nexus.io" },
  { id: "sec-012", name: "scorpion-api-token", type: "Bearer", last_rotated: "2026-02-01", next_rotation: "2026-05-01", status: "expired", version: 2, created_by: "ops@nexus.io" },
];

export async function GET() {
  return Response.json(secrets);
}
