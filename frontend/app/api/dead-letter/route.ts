import { NextResponse } from "next/server";

interface DLQEvent {
  id: string;
  uuid: string;
  original_topic: string;
  action: string;
  payload: Record<string, unknown>;
  failed_at: string;
  failure_reason: string;
  retry_count: number;
  source: string;
}

const DEAD_LETTERS: DLQEvent[] = Array.from({ length: 25 }, (_, i) => ({
  id: `dlq-${String(i).padStart(4, "0")}`,
  uuid: `deadbeef-${String(i).padStart(8, "0")}-${String(100 + i).padStart(8, "0")}`,
  original_topic: ["inventory.lock", "watchdog.check", "phoenix.recover", "reconciliation.sync", "twin.update"][Math.floor(Math.random() * 5)],
  action: ["lock", "check", "recover", "sync", "update"][Math.floor(Math.random() * 5)],
  payload: { reason: "timeout", attempt: Math.floor(Math.random() * 3) + 1 },
  failed_at: new Date(Date.now() - i * 300000).toISOString(),
  failure_reason: ["timeout", "max_retries_exceeded", "invalid_payload", "worker_unavailable", "circuit_breaker_open"][Math.floor(Math.random() * 5)],
  retry_count: Math.floor(Math.random() * 5) + 1,
  source: ["inventory", "scorpion", "reconciliation", "twin", "watchdog"][Math.floor(Math.random() * 5)],
}));

export async function GET() {
  return NextResponse.json({ events: DEAD_LETTERS, total: DEAD_LETTERS.length });
}
