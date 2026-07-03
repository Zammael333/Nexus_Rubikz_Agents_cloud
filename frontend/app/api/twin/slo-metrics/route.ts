import { NextResponse } from "next/server";

const TWIN_BASE = process.env.TWIN_API_URL || "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${TWIN_BASE}/api/v1/twin/slo-metrics`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      slo_target: 99.9973,
      slo_current: 99.9973,
      error_budget_total: 0.0027,
      error_budget_remaining: 0.0027,
      total_requests: 0,
      total_failures: 0,
      error_rate_percent: 0,
      budget_consumed_percent: 0,
      allowed_failures_remaining: 0,
      budget_status: "healthy",
      budget_history: [],
    });
  }
}
