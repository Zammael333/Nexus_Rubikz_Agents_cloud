export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: number;
  severity: "critical" | "warning" | "info";
  interval: string;
  enabled: boolean;
  last_fired: string | null;
}

const rules: AlertRule[] = [
  { id: "ar-001", name: "CPU > 90%", metric: "cpu_usage", condition: ">", threshold: 90, severity: "critical", interval: "5m", enabled: true, last_fired: "2026-06-30T14:23:00Z" },
  { id: "ar-002", name: "Memory > 85%", metric: "memory_usage", condition: ">", threshold: 85, severity: "warning", interval: "5m", enabled: true, last_fired: "2026-06-30T12:10:00Z" },
  { id: "ar-003", name: "Error Rate > 5%", metric: "error_rate", condition: ">", threshold: 5, severity: "critical", interval: "1m", enabled: true, last_fired: "2026-06-30T13:45:00Z" },
  { id: "ar-004", name: "P99 Latency > 500ms", metric: "latency_p99", condition: ">", threshold: 500, severity: "warning", interval: "1m", enabled: true, last_fired: "2026-06-29T09:30:00Z" },
  { id: "ar-005", name: "Disk > 80%", metric: "disk_usage", condition: ">", threshold: 80, severity: "warning", interval: "10m", enabled: true, last_fired: null },
  { id: "ar-006", name: "Throughput < 10 rpm", metric: "throughput", condition: "<", threshold: 10, severity: "critical", interval: "5m", enabled: false, last_fired: "2026-06-28T16:00:00Z" },
  { id: "ar-007", name: "Connection Drops > 1%", metric: "drop_rate", condition: ">", threshold: 1, severity: "warning", interval: "5m", enabled: true, last_fired: "2026-06-30T11:00:00Z" },
  { id: "ar-008", name: "SLO < 99.99%", metric: "slo_current", condition: "<", threshold: 99.99, severity: "critical", interval: "1m", enabled: true, last_fired: null },
  { id: "ar-009", name: "Queue Depth > 1000", metric: "queue_depth", condition: ">", threshold: 1000, severity: "warning", interval: "5m", enabled: true, last_fired: "2026-06-29T22:15:00Z" },
  { id: "ar-010", name: "Certificate Expiry < 7d", metric: "cert_days_left", condition: "<", threshold: 7, severity: "critical", interval: "1h", enabled: true, last_fired: "2026-06-30T08:00:00Z" },
  { id: "ar-011", name: "Budget Consumption > 80%", metric: "budget_consumed", condition: ">", threshold: 80, severity: "warning", interval: "5m", enabled: true, last_fired: "2026-06-30T10:30:00Z" },
  { id: "ar-012", name: "Health Check Failures", metric: "health_fails", condition: ">", threshold: 3, severity: "critical", interval: "1m", enabled: true, last_fired: "2026-06-30T14:00:00Z" },
];

export async function GET() {
  return Response.json(rules);
}
