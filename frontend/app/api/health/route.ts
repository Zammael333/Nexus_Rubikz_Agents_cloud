import { NextResponse } from "next/server";

const WORKER_HEALTH = [
  { id: "w-inventory", label: "Inventory", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 12, memory: 34, latency_ms: 45, last_check: "2026-07-01T02:30:00Z", trust_score: 0.97, sandbox: false, phoenix: true, budget_frozen: false },
  { id: "w-watchdog", label: "Watchdog", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 8, memory: 22, latency_ms: 12, last_check: "2026-07-01T02:30:00Z", trust_score: 0.99, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-scorpion", label: "Scorpion Scanner", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 45, memory: 67, latency_ms: 120, last_check: "2026-07-01T02:30:00Z", trust_score: 0.95, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-notifier", label: "Notifier", status: "degraded", pulse: "yellow", uptime: "14d 7h", cpu: 22, memory: 41, latency_ms: 230, last_check: "2026-07-01T02:29:00Z", trust_score: 0.93, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-phoenix", label: "Phoenix Protocol", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 5, memory: 18, latency_ms: 8, last_check: "2026-07-01T02:30:00Z", trust_score: 1.0, sandbox: false, phoenix: true, budget_frozen: false },
  { id: "w-budget", label: "Budget Watchdog", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 6, memory: 15, latency_ms: 15, last_check: "2026-07-01T02:30:00Z", trust_score: 0.98, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-sat-shield", label: "SAT Shield", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 10, memory: 28, latency_ms: 35, last_check: "2026-07-01T02:30:00Z", trust_score: 0.96, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-reconciliation", label: "Reconciliation", status: "standby", pulse: "yellow", uptime: "14d 7h", cpu: 3, memory: 12, latency_ms: 5, last_check: "2026-07-01T02:28:00Z", trust_score: 0.91, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-twin", label: "Digital Twin", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 18, memory: 55, latency_ms: 60, last_check: "2026-07-01T02:30:00Z", trust_score: 0.94, sandbox: false, phoenix: true, budget_frozen: false },
  { id: "w-sandbox", label: "Sandbox", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 25, memory: 48, latency_ms: 90, last_check: "2026-07-01T02:30:00Z", trust_score: 0.92, sandbox: true, phoenix: false, budget_frozen: true },
  { id: "w-otel", label: "OTEL Injector", status: "healthy", pulse: "green", uptime: "14d 7h", cpu: 14, memory: 31, latency_ms: 22, last_check: "2026-07-01T02:30:00Z", trust_score: 0.97, sandbox: false, phoenix: false, budget_frozen: false },
  { id: "w-red-team", label: "Red Team", status: "standby", pulse: "orange", uptime: "14d 7h", cpu: 60, memory: 72, latency_ms: 350, last_check: "2026-07-01T02:00:00Z", trust_score: 0.88, sandbox: false, phoenix: false, budget_frozen: false },
];

export async function GET() {
  return NextResponse.json({ workers: WORKER_HEALTH });
}
