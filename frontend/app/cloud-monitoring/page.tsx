"use client";

export default function CloudMonitoringPage() {
  const metrics = [
    { name: "Compute Engine CPU", value: "23%", status: "ok", link: "https://console.cloud.google.com/monitoring" },
    { name: "Cloud SQL Connections", value: "47", status: "ok", link: "https://console.cloud.google.com/sql" },
    { name: "Cloud Run Latency", value: "210ms p99", status: "warning", link: "https://console.cloud.google.com/run" },
    { name: "GKE Cluster Usage", value: "34%", status: "ok", link: "https://console.cloud.google.com/kubernetes" },
    { name: "Cloud Storage Requests", value: "1.2K/min", status: "ok", link: "https://console.cloud.google.com/storage" },
    { name: "Pub/Sub Backlog", value: "12 messages", status: "ok", link: "https://console.cloud.google.com/pubsub" },
    { name: "Cloud Logging Errors", value: "0.002%", status: "ok", link: "https://console.cloud.google.com/logs" },
    { name: "Cloud Trace Spans", value: "12.5K/24h", status: "ok", link: "https://console.cloud.google.com/traces" },
    { name: "Alerting Policy Violations", value: "2 active", status: "warning", link: "https://console.cloud.google.com/monitoring/alerting" },
  ];

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Cloud Monitoring</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">GCP Monitoring integration — alerts, metrics, dashboards</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {metrics.map((m) => (
          <a
            key={m.name}
            href={m.link}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-nexus-surface border border-nexus-border rounded-lg p-4 hover:border-nexus-border/80 transition-colors block"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-nexus-muted uppercase tracking-wider">{m.name}</span>
              <span className={`w-2 h-2 rounded-full ${m.status === "ok" ? "bg-edge-green" : "bg-edge-yellow"}`} />
            </div>
            <div className="text-sm font-bold text-nexus-text font-mono">{m.value}</div>
            <div className="text-[9px] text-edge-green mt-2 uppercase tracking-wider">Open in GCP →</div>
          </a>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-3">Active Alerts</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-nexus-bg rounded border-l-2 border-edge-yellow">
              <div>
                <div className="text-[10px] text-nexus-text">Cloud Run P99 Latency {">"} 200ms</div>
                <div className="text-[9px] text-nexus-muted">Triggered 10 min ago</div>
              </div>
              <a href="https://console.cloud.google.com/monitoring/alerting" target="_blank" rel="noopener noreferrer" className="text-[9px] text-edge-green uppercase tracking-wider hover:underline">
                View
              </a>
            </div>
            <div className="flex items-center justify-between p-2 bg-nexus-bg rounded border-l-2 border-edge-yellow">
              <div>
                <div className="text-[10px] text-nexus-text">Notification Queue Depth {">"} 100</div>
                <div className="text-[9px] text-nexus-muted">Triggered 25 min ago</div>
              </div>
              <a href="https://console.cloud.google.com/monitoring/alerting" target="_blank" rel="noopener noreferrer" className="text-[9px] text-edge-green uppercase tracking-wider hover:underline">
                View
              </a>
            </div>
          </div>
        </div>

        <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
          <h2 className="text-xs font-bold text-nexus-text uppercase tracking-wider mb-3">SLO Compliance</h2>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-nexus-muted">API Availability</span>
                <span className="text-edge-green">99.998%</span>
              </div>
              <div className="h-2 bg-nexus-bg rounded-full overflow-hidden">
                <div className="h-full bg-edge-green rounded-full" style={{ width: "99.998%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-nexus-muted">P99 Latency</span>
                <span className="text-edge-yellow">120ms / 200ms target</span>
              </div>
              <div className="h-2 bg-nexus-bg rounded-full overflow-hidden">
                <div className="h-full bg-edge-yellow rounded-full" style={{ width: "60%" }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-nexus-muted">Error Rate</span>
                <span className="text-edge-green">0.002% / 0.1% target</span>
              </div>
              <div className="h-2 bg-nexus-bg rounded-full overflow-hidden">
                <div className="h-full bg-edge-green rounded-full" style={{ width: "2%" }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
