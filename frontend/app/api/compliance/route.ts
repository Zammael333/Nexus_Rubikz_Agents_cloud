export interface ComplianceCheck {
  id: string;
  framework: string;
  control: string;
  description: string;
  status: "pass" | "fail" | "warning" | "not_applicable";
  last_checked: string;
  evidence: string;
  owner: string;
}

const checks: ComplianceCheck[] = [
  { id: "cmp-001", framework: "SOC 2", control: "CC6.1", description: "Logical and physical access controls", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "Access audit log reviewed", owner: "security@nexus.io" },
  { id: "cmp-002", framework: "SOC 2", control: "CC7.2", description: "Monitoring of system components", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "Monitoring dashboards active", owner: "sre@nexus.io" },
  { id: "cmp-003", framework: "SOC 2", control: "CC7.3", description: "Incident response plan", status: "warning", last_checked: "2026-06-29T06:00:00Z", evidence: "Response plan exists but untested for 90 days", owner: "sre@nexus.io" },
  { id: "cmp-004", framework: "ISO 27001", control: "A.9.2.1", description: "User registration and de-registration", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "JIT provisioning active", owner: "security@nexus.io" },
  { id: "cmp-005", framework: "ISO 27001", control: "A.12.4.1", description: "Event logging", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "Centralized logging active", owner: "sre@nexus.io" },
  { id: "cmp-006", framework: "ISO 27001", control: "A.12.6.1", description: "Vulnerability management", status: "fail", last_checked: "2026-06-28T06:00:00Z", evidence: "3 CVEs past remediation SLA", owner: "security@nexus.io" },
  { id: "cmp-007", framework: "GDPR", control: "Art. 32", description: "Security of processing", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "Encryption at rest and in transit", owner: "dpo@nexus.io" },
  { id: "cmp-008", framework: "GDPR", control: "Art. 33", description: "Breach notification", status: "not_applicable", last_checked: "2026-06-30T06:00:00Z", evidence: "No breaches in period", owner: "dpo@nexus.io" },
  { id: "cmp-009", framework: "SOC 2", control: "CC6.6", description: "Logical access security measures", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "MFA enforced for all users", owner: "security@nexus.io" },
  { id: "cmp-010", framework: "ISO 27001", control: "A.8.2.3", description: "Handling of assets", status: "warning", last_checked: "2026-06-29T06:00:00Z", evidence: "3 assets missing classification tags", owner: "ops@nexus.io" },
  { id: "cmp-011", framework: "GDPR", control: "Art. 5", description: "Data minimization", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "Retention policies enforced", owner: "dpo@nexus.io" },
  { id: "cmp-012", framework: "SOC 2", control: "CC6.2", description: "System authentication", status: "pass", last_checked: "2026-06-30T06:00:00Z", evidence: "SPIFFE/SPIRE identity active", owner: "security@nexus.io" },
];

export async function GET() {
  return Response.json(checks);
}
