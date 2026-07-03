export interface CostEntry {
  id: string;
  service: string;
  category: string;
  monthly_cost: number;
  trend_pct: number;
  budget: number;
  projects: { name: string; cost: number }[];
}

const costs: CostEntry[] = [
  { id: "cost-001", service: "Compute Engine", category: "compute", monthly_cost: 12450.00, trend_pct: 3.2, budget: 15000, projects: [{ name: "nexus-prod", cost: 8900 }, { name: "nexus-staging", cost: 2550 }, { name: "nexus-dev", cost: 1000 }] },
  { id: "cost-002", service: "Cloud Storage", category: "storage", monthly_cost: 3200.00, trend_pct: -1.5, budget: 4000, projects: [{ name: "nexus-prod", cost: 2100 }, { name: "nexus-backups", cost: 1100 }] },
  { id: "cost-003", service: "Cloud SQL", category: "database", monthly_cost: 4800.00, trend_pct: 0.0, budget: 5000, projects: [{ name: "nexus-prod", cost: 3800 }, { name: "nexus-staging", cost: 1000 }] },
  { id: "cost-004", service: "Cloud Load Balancing", category: "network", monthly_cost: 2100.00, trend_pct: 5.8, budget: 2500, projects: [{ name: "nexus-prod", cost: 2100 }] },
  { id: "cost-005", service: "Cloud NAT", category: "network", monthly_cost: 850.00, trend_pct: 2.1, budget: 1000, projects: [{ name: "nexus-prod", cost: 850 }] },
  { id: "cost-006", service: "Cloud Monitoring", category: "observability", monthly_cost: 1650.00, trend_pct: 12.4, budget: 2000, projects: [{ name: "nexus-prod", cost: 1200 }, { name: "nexus-staging", cost: 450 }] },
  { id: "cost-007", service: "Cloud KMS", category: "security", monthly_cost: 420.00, trend_pct: 0.0, budget: 500, projects: [{ name: "nexus-prod", cost: 420 }] },
  { id: "cost-008", service: "Cloud CDN", category: "network", monthly_cost: 980.00, trend_pct: -3.2, budget: 1500, projects: [{ name: "nexus-prod", cost: 980 }] },
  { id: "cost-009", service: "BigQuery", category: "analytics", monthly_cost: 5600.00, trend_pct: 8.5, budget: 6000, projects: [{ name: "nexus-prod", cost: 4200 }, { name: "nexus-analytics", cost: 1400 }] },
  { id: "cost-010", service: "Cloud Run", category: "compute", monthly_cost: 3400.00, trend_pct: 15.2, budget: 4000, projects: [{ name: "nexus-prod", cost: 2400 }, { name: "nexus-staging", cost: 1000 }] },
];

export async function GET() {
  return Response.json(costs);
}
