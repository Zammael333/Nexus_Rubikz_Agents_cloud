import { NextResponse } from "next/server";

const WORKER_STATE = {
  kernel: {
    inventory: { active_locks: 3, pending_tx: 7, sku_count: 142, last_scan: "2026-07-01T02:30:00Z" },
    watchdog: { status: "armed", detectors: 12, alerts_24h: 2 },
    phoenix: { health: "nominal", rto_avg_ms: 1800, recoveries: 47 },
    budget: { slo_current: 99.9973, error_budget_remaining: 0.0027, budget_used_24h: 0.0012 },
    scorpion: { last_scan: "2026-07-01T02:00:00Z", issues_found: 0, dead_stock_count: 5 },
    notifier: { pending: 0, sent_24h: 34, failures: 0 },
    reconciliation: { last_da: 0.0031, ledger_diff: 0.0008, status: "nominal" },
    "sat-shield": { da_threshold: 0.01, current_da: 0.0031, last_verification: "2026-07-01T02:15:00Z" },
    "red-team": { last_simulation: "2026-06-30T18:00:00Z", findings: 2, critical: 0 },
    twin: { fidelity: 99.98, last_sync: "2026-07-01T02:29:00Z" },
    sandbox: { isolated_workers: 0, total_cages: 10, active_cages: 8 },
    otel: { spans_exported_24h: 12500, errors: 0, queue_depth: 3 },
  },
  twin_state: {
    inventory: { active_locks: 3, pending_tx: 7, sku_count: 142 },
    watchdog: { status: "armed", alerts_24h: 2 },
    phoenix: { health: "nominal", rto_avg_ms: 1820 },
    budget: { slo_current: 99.9973, error_budget_remaining: 0.0027 },
  },
};

export async function GET() {
  return NextResponse.json(WORKER_STATE);
}
