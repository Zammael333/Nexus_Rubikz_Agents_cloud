import { NextResponse } from "next/server";

function makeDate(daysAgo: number, minutesAgo: number) {
  const d = new Date("2026-07-01T00:00:00Z");
  d.setDate(d.getDate() - daysAgo);
  d.setMinutes(d.getMinutes() - minutesAgo);
  return d.toISOString();
}

const RECOVERIES = Array.from({ length: 25 }, (_, i) => {
  const downtime_min = 0.5 + Math.random() * 5;
  return {
    id: `phx-${i + 1}`,
    worker: ["inventory", "notifier", "red-team", "twin", "scorpion"][i % 5],
    triggered_at: makeDate(i, Math.floor(Math.random() * 720)),
    recovered_at: makeDate(i, Math.floor(Math.random() * 720) - Math.round(downtime_min)),
    downtime_minutes: Math.round(downtime_min * 10) / 10,
    rto_met: downtime_min < 4,
    cause: ["OOM", "hang", "crash", "timeout", "panic"][i % 5],
    action: ["restart", "rollback", "scale-up", "fence", "reimage"][i % 5],
  };
}).reverse();

export async function GET() {
  return NextResponse.json({ recoveries: RECOVERIES });
}
