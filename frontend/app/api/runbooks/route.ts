export interface Runbook {
  id: string;
  title: string;
  category: string;
  description: string;
  steps: number;
  last_reviewed: string;
  owner: string;
  avg_duration_min: number;
}

const runbooks: Runbook[] = [
  { id: "rb-001", title: "Worker CPU Spike Response", category: "incident", description: "Diagnose and mitigate sudden CPU spikes on any worker", steps: 8, last_reviewed: "2026-06-15", owner: "sre@nexus.io", avg_duration_min: 15 },
  { id: "rb-002", title: "Dead-Letter Queue Drain", category: "operations", description: "Drain and reprocess events from dead-letter queue", steps: 6, last_reviewed: "2026-06-10", owner: "ops@nexus.io", avg_duration_min: 20 },
  { id: "rb-003", title: "SVID Certificate Renewal", category: "security", description: "Manual SPIFFE SVID renewal when auto-renewal fails", steps: 5, last_reviewed: "2026-06-20", owner: "security@nexus.io", avg_duration_min: 10 },
  { id: "rb-004", title: "Database Failover Procedure", category: "incident", description: "Promote standby database to primary during failure", steps: 12, last_reviewed: "2026-05-28", owner: "dba@nexus.io", avg_duration_min: 25 },
  { id: "rb-005", title: "Cluster Node Drain", category: "operations", description: "Safely drain a Kubernetes node for maintenance", steps: 7, last_reviewed: "2026-06-22", owner: "sre@nexus.io", avg_duration_min: 12 },
  { id: "rb-006", title: "Phoenix Recovery Trigger", category: "incident", description: "Trigger and monitor Phoenix protocol worker recovery", steps: 9, last_reviewed: "2026-06-25", owner: "sre@nexus.io", avg_duration_min: 30 },
  { id: "rb-007", title: "Backup Integrity Verification", category: "operations", description: "Verify backup checksums and perform test restore", steps: 4, last_reviewed: "2026-06-18", owner: "ops@nexus.io", avg_duration_min: 45 },
  { id: "rb-008", title: "Incident Post-Mortem Template", category: "process", description: "Structured post-incident analysis and documentation", steps: 6, last_reviewed: "2026-06-01", owner: "sre@nexus.io", avg_duration_min: 60 },
  { id: "rb-009", title: "Secrets Rotation Playbook", category: "security", description: "Rotate API keys, tokens, and service account credentials", steps: 7, last_reviewed: "2026-06-20", owner: "security@nexus.io", avg_duration_min: 20 },
  { id: "rb-010", title: "Cloud Cost Anomaly Investigation", category: "process", description: "Investigate and remediate unexpected cloud cost spikes", steps: 5, last_reviewed: "2026-06-12", owner: "finance@nexus.io", avg_duration_min: 35 },
  { id: "rb-011", title: "Maintenance Window Execution", category: "operations", description: "Execute planned maintenance with rollback plan", steps: 10, last_reviewed: "2026-06-22", owner: "sre@nexus.io", avg_duration_min: 40 },
  { id: "rb-012", title: "Alert Rule Tuning", category: "process", description: "Tune alert thresholds to reduce noise and prevent fatigue", steps: 4, last_reviewed: "2026-06-19", owner: "sre@nexus.io", avg_duration_min: 15 },
];

export async function GET() {
  return Response.json(runbooks);
}
