import { NextResponse } from "next/server";

const TIMELINE = [
  { timestamp: "2026-06-30T00:00:00Z", kernel: { inventory: { active_locks: 3 }, phoenix: { health: "nominal" } }, twin: { inventory: { active_locks: 3 }, phoenix: { health: "nominal" } }, diff_count: 0 },
  { timestamp: "2026-06-30T06:00:00Z", kernel: { inventory: { active_locks: 5 }, phoenix: { health: "nominal" } }, twin: { inventory: { active_locks: 5 }, phoenix: { health: "nominal" } }, diff_count: 0 },
  { timestamp: "2026-06-30T12:00:00Z", kernel: { inventory: { active_locks: 2 }, phoenix: { health: "degraded" } }, twin: { inventory: { active_locks: 2 }, phoenix: { health: "nominal" } }, diff_count: 1 },
  { timestamp: "2026-06-30T18:00:00Z", kernel: { inventory: { active_locks: 4 }, phoenix: { health: "nominal" } }, twin: { inventory: { active_locks: 4 }, phoenix: { health: "nominal" } }, diff_count: 0 },
  { timestamp: "2026-07-01T00:00:00Z", kernel: { inventory: { active_locks: 7 }, phoenix: { health: "nominal" } }, twin: { inventory: { active_locks: 7 }, phoenix: { health: "nominal" } }, diff_count: 0 },
  { timestamp: "2026-07-01T02:00:00Z", kernel: { inventory: { active_locks: 3 }, phoenix: { health: "critical" } }, twin: { inventory: { active_locks: 3 }, phoenix: { health: "nominal" } }, diff_count: 1 },
];

export async function GET() {
  return NextResponse.json({ timeline: TIMELINE });
}
