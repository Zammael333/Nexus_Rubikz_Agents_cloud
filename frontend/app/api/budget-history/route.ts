import { NextResponse } from "next/server";

const HISTORY = Array.from({ length: 30 }, (_, i) => {
  const d = new Date("2026-06-01T00:00:00Z");
  d.setDate(d.getDate() + i);
  const consumed = 0.0004 + Math.random() * 0.0006;
  return {
    date: d.toISOString().split("T")[0],
    budget_remaining: Math.max(0, 0.0027 - (i + 1) * 0.00008),
    budget_consumed: consumed,
    slo_achieved: 99.997 + Math.random() * 0.001,
  };
});

export async function GET() {
  return NextResponse.json({ history: HISTORY });
}
