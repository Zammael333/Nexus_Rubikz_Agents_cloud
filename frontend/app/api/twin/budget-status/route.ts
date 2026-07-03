import { NextResponse } from "next/server";

const TWIN_BASE = process.env.TWIN_API_URL || "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${TWIN_BASE}/api/v1/twin/budget-status`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      report: {
        total_requests: 0,
        total_failures: 0,
        error_rate_percent: 0,
        budget_consumed_percent: 0,
        status: "healthy",
        allowed_failures_remaining: 0,
        window_seconds: 2592000,
        timestamp: Date.now() / 1000,
      },
      is_frozen: false,
      warning_threshold: 50,
      freeze_threshold: 100,
      window_hours: 720,
    });
  }
}
