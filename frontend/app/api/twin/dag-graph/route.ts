import { NextResponse } from "next/server";

const TWIN_BASE = process.env.TWIN_API_URL || "http://localhost:8001";

const FALLBACK_GRAPH = {
  nodes: [
    { id: "kernel", label: "Kernel", type: "hub" },
    { id: "twin", label: "Digital Twin", type: "twin" },
    { id: "inventory", label: "Inventory", type: "worker" },
    { id: "watchdog", label: "Watchdog", type: "worker" },
    { id: "phoenix", label: "Phoenix", type: "worker" },
    { id: "scorpion", label: "Scorpion", type: "scanner" },
    { id: "sat-shield", label: "SAT Shield", type: "validator" },
    { id: "notifier", label: "Notifier", type: "worker" },
    { id: "budget", label: "Budget Watcher", type: "monitor" },
    { id: "edge-glow", label: "Edge Glow", type: "monitor" },
    { id: "sandbox", label: "Sandbox", type: "isolator" },
    { id: "otel", label: "OpenTelemetry", type: "telemetry" },
  ],
  edges: [
    { source: "kernel", target: "twin", protocol: "a2a", status: "active" },
    { source: "kernel", target: "inventory", protocol: "internal", status: "active" },
    { source: "kernel", target: "watchdog", protocol: "internal", status: "active" },
    { source: "phoenix", target: "kernel", protocol: "health", status: "active" },
    { source: "budget", target: "kernel", protocol: "slo", status: "active" },
    { source: "edge-glow", target: "budget", protocol: "pulse", status: "active" },
    { source: "scorpion", target: "kernel", protocol: "scan", status: "active" },
    { source: "sat-shield", target: "kernel", protocol: "da", status: "active" },
    { source: "notifier", target: "kernel", protocol: "alert", status: "active" },
    { source: "sandbox", target: "kernel", protocol: "isolate", status: "active" },
    { source: "otel", target: "kernel", protocol: "telemetry", status: "active" },
    { source: "otel", target: "twin", protocol: "telemetry", status: "active" },
  ],
  metadata: { pulse: "green", is_frozen: false },
};

export async function GET() {
  try {
    const res = await fetch(`${TWIN_BASE}/api/v1/twin/dag-graph`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(FALLBACK_GRAPH);
  }
}
