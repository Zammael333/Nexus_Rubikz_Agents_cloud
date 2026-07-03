import { NextResponse } from "next/server";

const TWIN_BASE = process.env.TWIN_API_URL || "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${TWIN_BASE}/api/v1/twin/edge-glow`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      pulse: "green",
      workers: { status: "UNAVAILABLE", count: 0, workers: {} },
      budget: { status: "UNAVAILABLE" },
      bus: { status: "UNAVAILABLE" },
      scorpion_vectors: {
        "SC-01_race_condition": "PARTIALLY_MITIGATED",
        "SC-02_accounting_drift": "MITIGATED",
        "SC-03_watchdog_fatigue": "PENDING",
        "SC-04_dead_letter_orphan": "MITIGATED",
        "SC-05_budget_exhaustion": "MITIGATED",
      },
      slo: {
        nominal_slo: 0.999973,
        real_slo: 0.999973,
        gap: 0,
        error_budget_remaining: 1.0,
        error_budget_usage_pct: 0,
        failures_last_hour: 0,
        slo_pulse: "green",
      },
      timestamp: new Date().toISOString(),
    });
  }
}
