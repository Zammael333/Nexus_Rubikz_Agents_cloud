import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    slo_target: 99.9973,
    slo_current: 99.9973,
    error_budget_total: 0.0027,
    error_budget_remaining: 0.0015,
    error_budget_consumed_24h: 0.0012,
    monthly_allowance_failures: 44,
    failures_this_month: 12,
    budget_history: [
      { date: "2026-06-01", remaining: 0.0027 },
      { date: "2026-06-05", remaining: 0.0025 },
      { date: "2026-06-10", remaining: 0.0023 },
      { date: "2026-06-15", remaining: 0.0021 },
      { date: "2026-06-20", remaining: 0.0019 },
      { date: "2026-06-25", remaining: 0.0017 },
      { date: "2026-06-30", remaining: 0.0015 },
    ],
    sli_breakdown: {
      availability: 99.998,
      latency_p99_ms: 120,
      throughput_rpm: 4200,
      error_rate_pct: 0.002,
    },
  });
}
