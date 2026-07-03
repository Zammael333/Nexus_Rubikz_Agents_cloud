import { NextResponse } from "next/server";

interface SPIFFEIdentity {
  id: string;
  spiffe_id: string;
  worker: string;
  status: string;
  issued_at: string;
  expires_at: string;
  ttl_hours: number;
  last_used: string;
}

const IDENTITIES: SPIFFEIdentity[] = [
  { id: "spiffe-001", spiffe_id: "spiffe://nexus-rubykz.io/worker/inventory", worker: "inventory", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:30:00Z" },
  { id: "spiffe-002", spiffe_id: "spiffe://nexus-rubykz.io/worker/scorpion", worker: "scorpion", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:28:00Z" },
  { id: "spiffe-003", spiffe_id: "spiffe://nexus-rubykz.io/worker/reconciliation", worker: "reconciliation", status: "valid", issued_at: "2026-06-10T00:00:00Z", expires_at: "2026-09-10T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:29:00Z" },
  { id: "spiffe-004", spiffe_id: "spiffe://nexus-rubykz.io/worker/phoenix", worker: "phoenix", status: "valid", issued_at: "2026-06-15T00:00:00Z", expires_at: "2026-09-15T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:27:00Z" },
  { id: "spiffe-005", spiffe_id: "spiffe://nexus-rubykz.io/worker/twin", worker: "twin", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:25:00Z" },
  { id: "spiffe-006", spiffe_id: "spiffe://nexus-rubykz.io/worker/watchdog", worker: "watchdog", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:20:00Z" },
  { id: "spiffe-007", spiffe_id: "spiffe://nexus-rubykz.io/worker/notifier", worker: "notifier", status: "expiring", issued_at: "2026-04-01T00:00:00Z", expires_at: "2026-07-05T00:00:00Z", ttl_hours: 96, last_used: "2026-07-01T02:10:00Z" },
  { id: "spiffe-008", spiffe_id: "spiffe://nexus-rubykz.io/worker/sat-shield", worker: "sat-shield", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-07-01T02:15:00Z" },
  { id: "spiffe-009", spiffe_id: "spiffe://nexus-rubykz.io/worker/red-team", worker: "red-team", status: "valid", issued_at: "2026-06-01T00:00:00Z", expires_at: "2026-09-01T00:00:00Z", ttl_hours: 2160, last_used: "2026-06-30T18:00:00Z" },
  { id: "spiffe-010", spiffe_id: "spiffe://nexus-rubykz.io/worker/sandbox", worker: "sandbox", status: "revoked", issued_at: "2026-05-01T00:00:00Z", expires_at: "2026-06-01T00:00:00Z", ttl_hours: 744, last_used: "2026-05-30T12:00:00Z" },
];

export async function GET() {
  return NextResponse.json({ identities: IDENTITIES, total: IDENTITIES.length });
}
