import { NextResponse } from "next/server";

const TRACES = [
  {
    trace_id: "trace-001",
    spans: [
      { span_id: "span-001a", name: "GET /api/inventory", parent_id: null, duration_ms: 450, start_time: "2026-07-01T02:30:00.000Z", status: "ok" },
      { span_id: "span-001b", name: "db.query", parent_id: "span-001a", duration_ms: 200, start_time: "2026-07-01T02:30:00.050Z", status: "ok" },
      { span_id: "span-001c", name: "cache.get", parent_id: "span-001a", duration_ms: 80, start_time: "2026-07-01T02:30:00.260Z", status: "ok" },
      { span_id: "span-001d", name: "serialize", parent_id: "span-001a", duration_ms: 120, start_time: "2026-07-01T02:30:00.350Z", status: "ok" },
    ],
  },
  {
    trace_id: "trace-002",
    spans: [
      { span_id: "span-002a", name: "POST /api/transactions", parent_id: null, duration_ms: 1200, start_time: "2026-07-01T02:30:05.000Z", status: "ok" },
      { span_id: "span-002b", name: "auth.verify", parent_id: "span-002a", duration_ms: 150, start_time: "2026-07-01T02:30:05.010Z", status: "ok" },
      { span_id: "span-002c", name: "db.write", parent_id: "span-002a", duration_ms: 800, start_time: "2026-07-01T02:30:05.200Z", status: "error" },
      { span_id: "span-002d", name: "queue.publish", parent_id: "span-002a", duration_ms: 100, start_time: "2026-07-01T02:30:06.050Z", status: "ok" },
    ],
  },
  {
    trace_id: "trace-003",
    spans: [
      { span_id: "span-003a", name: "GET /api/health", parent_id: null, duration_ms: 90, start_time: "2026-07-01T02:31:00.000Z", status: "ok" },
    ],
  },
];

export async function GET() {
  return NextResponse.json({ traces: TRACES });
}
