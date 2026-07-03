export interface TopologyNode {
  id: string;
  name: string;
  type: "service" | "worker" | "database" | "external" | "queue";
  status: "healthy" | "degraded" | "down";
  dependencies: string[];
}

export interface TopologyEdge {
  source: string;
  target: string;
  protocol: string;
  latency_p99_ms: number;
  error_rate_pct: number;
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

const nodes: TopologyNode[] = [
  { id: "api-gateway", name: "API Gateway", type: "service", status: "healthy", dependencies: ["auth-service", "worker-dispatcher"] },
  { id: "auth-service", name: "Auth Service", type: "service", status: "healthy", dependencies: ["spire-agent", "user-db"] },
  { id: "spire-agent", name: "SPIRE Agent", type: "worker", status: "healthy", dependencies: [] },
  { id: "user-db", name: "User Database", type: "database", status: "healthy", dependencies: [] },
  { id: "worker-dispatcher", name: "Worker Dispatcher", type: "service", status: "healthy", dependencies: ["event-queue", "watchdog", "notifier", "sensor"] },
  { id: "event-queue", name: "Event Queue", type: "queue", status: "healthy", dependencies: [] },
  { id: "watchdog", name: "Watchdog", type: "worker", status: "degraded", dependencies: ["health-store"] },
  { id: "health-store", name: "Health Store", type: "database", status: "healthy", dependencies: [] },
  { id: "notifier", name: "Notifier", type: "worker", status: "healthy", dependencies: ["webhook-proxy"] },
  { id: "webhook-proxy", name: "Webhook Proxy", type: "external", status: "healthy", dependencies: [] },
  { id: "sensor", name: "Sensor", type: "worker", status: "healthy", dependencies: ["metric-store"] },
  { id: "metric-store", name: "Metric Store", type: "database", status: "healthy", dependencies: [] },
  { id: "phoenix", name: "Phoenix Recovery", type: "worker", status: "healthy", dependencies: ["snapshot-store"] },
  { id: "snapshot-store", name: "Snapshot Store", type: "database", status: "healthy", dependencies: [] },
  { id: "dead-letter", name: "Dead Letter Queue", type: "queue", status: "healthy", dependencies: [] },
  { id: "graph-worker", name: "Graph Worker", type: "worker", status: "healthy", dependencies: ["graph-db"] },
  { id: "graph-db", name: "Graph Database", type: "database", status: "degraded", dependencies: [] },
];

const edges: TopologyEdge[] = [
  { source: "api-gateway", target: "auth-service", protocol: "gRPC", latency_p99_ms: 45, error_rate_pct: 0.02 },
  { source: "api-gateway", target: "worker-dispatcher", protocol: "gRPC", latency_p99_ms: 52, error_rate_pct: 0.05 },
  { source: "auth-service", target: "spire-agent", protocol: "http/2", latency_p99_ms: 28, error_rate_pct: 0.01 },
  { source: "auth-service", target: "user-db", protocol: "postgres", latency_p99_ms: 15, error_rate_pct: 0.03 },
  { source: "worker-dispatcher", target: "event-queue", protocol: "pubsub", latency_p99_ms: 12, error_rate_pct: 0.00 },
  { source: "worker-dispatcher", target: "watchdog", protocol: "gRPC", latency_p99_ms: 120, error_rate_pct: 2.10 },
  { source: "worker-dispatcher", target: "notifier", protocol: "gRPC", latency_p99_ms: 85, error_rate_pct: 0.15 },
  { source: "worker-dispatcher", target: "sensor", protocol: "gRPC", latency_p99_ms: 35, error_rate_pct: 0.08 },
  { source: "watchdog", target: "health-store", protocol: "pgx", latency_p99_ms: 22, error_rate_pct: 0.01 },
  { source: "notifier", target: "webhook-proxy", protocol: "https", latency_p99_ms: 210, error_rate_pct: 1.20 },
  { source: "sensor", target: "metric-store", protocol: "pgx", latency_p99_ms: 18, error_rate_pct: 0.02 },
  { source: "phoenix", target: "snapshot-store", protocol: "gRPC", latency_p99_ms: 65, error_rate_pct: 0.50 },
  { source: "dead-letter", target: "notifier", protocol: "gRPC", latency_p99_ms: 40, error_rate_pct: 0.00 },
  { source: "graph-worker", target: "graph-db", protocol: "bolt", latency_p99_ms: 30, error_rate_pct: 0.10 },
];

export async function GET() {
  return Response.json({ nodes, edges } satisfies TopologyData);
}
