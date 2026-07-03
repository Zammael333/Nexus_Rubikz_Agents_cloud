import { NextResponse } from "next/server";

const WORKERS = [
  { id: "w-inventory", label: "Inventory", status: "active", trust_score: 0.97, pulse: "green" },
  { id: "w-watchdog", label: "Watchdog", status: "active", trust_score: 0.99, pulse: "green" },
  { id: "w-scorpion", label: "Scorpion", status: "active", trust_score: 0.95, pulse: "green" },
  { id: "w-notifier", label: "Notifier", status: "active", trust_score: 0.93, pulse: "yellow" },
  { id: "w-phoenix", label: "Phoenix", status: "active", trust_score: 1.0, pulse: "green" },
  { id: "w-budget", label: "Budget Watchdog", status: "active", trust_score: 0.98, pulse: "green" },
  { id: "w-reconciliation", label: "Reconciliation", status: "standby", trust_score: 0.91, pulse: "yellow" },
  { id: "w-sat-shield", label: "SAT Shield", status: "active", trust_score: 0.96, pulse: "green" },
  { id: "w-red-team", label: "Red Team", status: "standby", trust_score: 0.88, pulse: "orange" },
  { id: "w-twin", label: "Digital Twin", status: "active", trust_score: 0.94, pulse: "green" },
  { id: "w-sandbox", label: "Sandbox", status: "active", trust_score: 0.92, pulse: "green" },
  { id: "w-otel", label: "OTEL Injector", status: "active", trust_score: 0.97, pulse: "green" },
];

const EDGES = [
  { source: "w-inventory", target: "w-scorpion", label: "A2A" },
  { source: "w-watchdog", target: "w-notifier", label: "A2A" },
  { source: "w-watchdog", target: "w-budget", label: "A2A" },
  { source: "w-phoenix", target: "w-watchdog", label: "A2A" },
  { source: "w-phoenix", target: "w-twin", label: "A2A" },
  { source: "w-reconciliation", target: "w-sat-shield", label: "DAG" },
  { source: "w-watchdog", target: "w-red-team", label: "DAG" },
  { source: "w-twin", target: "w-sandbox", label: "A2A" },
  { source: "w-otel", target: "w-watchdog", label: "OTEL" },
  { source: "w-otel", target: "w-inventory", label: "OTEL" },
  { source: "w-otel", target: "w-phoenix", label: "OTEL" },
  { source: "w-sat-shield", target: "w-reconciliation", label: "DAG" },
  { source: "w-scorpion", target: "w-notifier", label: "A2A" },
  { source: "w-sandbox", target: "w-inventory", label: "A2A" },
];

export async function GET() {
  return NextResponse.json({ workers: WORKERS, edges: EDGES });
}
