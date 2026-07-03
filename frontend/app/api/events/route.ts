import { NextResponse } from "next/server";

const SEVERITIES = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"] as const;

function randomEvent(idx: number) {
  const workers = ["inventory", "watchdog", "phoenix", "scorpion", "notifier", "reconciliation", "sat-shield", "red-team", "twin", "sandbox", "otel", "budget"];
  const severity = SEVERITIES[Math.floor(Math.random() * SEVERITIES.length)];
  const worker = workers[Math.floor(Math.random() * workers.length)];
  const actions = ["lock_acquired", "lock_released", "scan_complete", "health_check_ok", "alert_triggered", "budget_warning", "recovery_executed", "sync_completed", "anomaly_detected", "span_exported"];
  return {
    id: `evt-${String(idx).padStart(6, "0")}`,
    uuid: `550e8400-e29b-41d4-a716-44665544${String(idx).padStart(4, "0")}`,
    timestamp: new Date(Date.now() - idx * 45000).toISOString(),
    severity,
    worker,
    action: actions[Math.floor(Math.random() * actions.length)],
    payload: { detail: `Event #${idx} for ${worker}`, epoch: Math.floor(Math.random() * 100) },
    trace_id: idx % 3 === 0 ? `00-${Array(32).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join("")}-${Array(16).fill(0).map(() => Math.floor(Math.random() * 16).toString(16)).join("")}-01` : undefined,
  };
}

const EVENTS = Array.from({ length: 200 }, (_, i) => randomEvent(i));

export async function GET(request: Request) {
  const url = new URL(request.url);
  const severity = url.searchParams.get("severity");
  const worker = url.searchParams.get("worker");
  const query = url.searchParams.get("q")?.toLowerCase();
  const limit = Math.min(Number(url.searchParams.get("limit")) || 50, 200);

  let filtered = EVENTS;
  if (severity && severity !== "ALL") filtered = filtered.filter((e) => e.severity === severity);
  if (worker && worker !== "ALL") filtered = filtered.filter((e) => e.worker === worker);
  if (query) filtered = filtered.filter((e) => e.action.toLowerCase().includes(query) || e.worker.includes(query));

  const allWorkers = Array.from(new Set(EVENTS.map((e) => e.worker)));
  return NextResponse.json({ events: filtered.slice(0, limit), total: filtered.length, workers: allWorkers, severities: SEVERITIES });
}
