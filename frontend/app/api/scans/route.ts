import { NextResponse } from "next/server";

function makeDate(daysAgo: number, hour: number) {
  const d = new Date("2026-07-01T00:00:00Z");
  d.setDate(d.getDate() - daysAgo);
  d.setHours(hour);
  return d.toISOString();
}

const SCANS = Array.from({ length: 30 }, (_, i) => ({
  id: `scan-${i + 1}`,
  started_at: makeDate(i, 8 + (i % 12)),
  duration_sec: 30 + Math.floor(Math.random() * 300),
  items_scanned: 1000 + Math.floor(Math.random() * 4000),
  dead_stock_found: Math.floor(Math.random() * 8),
  anomalies: Math.floor(Math.random() * 3),
  status: Math.random() > 0.95 ? "failed" as const : "completed" as const,
}));

export async function GET() {
  return NextResponse.json({ scans: SCANS });
}
