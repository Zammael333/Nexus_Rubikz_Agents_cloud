import { NextResponse } from "next/server";

export async function GET() {
  const workers = [
    { label: "Inventory", cpu: 12, memory: 34, latency_ms: 45 },
    { label: "Watchdog", cpu: 8, memory: 22, latency_ms: 12 },
    { label: "Scorpion Scanner", cpu: 45, memory: 67, latency_ms: 120 },
    { label: "Notifier", cpu: 22, memory: 41, latency_ms: 230 },
    { label: "Phoenix Protocol", cpu: 5, memory: 18, latency_ms: 8 },
    { label: "Budget Watchdog", cpu: 6, memory: 15, latency_ms: 15 },
    { label: "SAT Shield", cpu: 10, memory: 28, latency_ms: 35 },
    { label: "Reconciliation", cpu: 3, memory: 12, latency_ms: 5 },
    { label: "Digital Twin", cpu: 18, memory: 55, latency_ms: 60 },
    { label: "Sandbox", cpu: 25, memory: 48, latency_ms: 90 },
    { label: "OTEL Injector", cpu: 14, memory: 31, latency_ms: 22 },
    { label: "Red Team", cpu: 60, memory: 72, latency_ms: 350 },
  ];

  const html = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>NEXUS-RUBYKZ Report</title>
<style>
  @page { margin: 20mm; }
  body { font-family: 'Courier New', monospace; font-size: 11px; color: #1a1a2e; }
  h1 { font-size: 18px; text-transform: uppercase; letter-spacing: 4px; border-bottom: 2px solid #00ff88; padding-bottom: 8px; }
  h2 { font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-top: 24px; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  th { background: #1a1a2e; color: #00ff88; padding: 6px 8px; text-align: left; font-size: 9px; text-transform: uppercase; letter-spacing: 1px; }
  td { padding: 4px 8px; border-bottom: 1px solid #ccc; }
  .green { color: #00aa55; }
  .yellow { color: #ccaa00; }
  .meta { color: #666; font-size: 9px; margin-top: 24px; text-align: center; }
</style></head><body>
<h1>NEXUS-RUBYKZ — System Health Report</h1>
<p style="color:#666;font-size:10px;">Generated: ${new Date().toISOString()} · SLO: 99.9973% · Error Budget: 0.0027%</p>
<h2>Worker Summary</h2>
<table><thead><tr><th>Worker</th><th>CPU</th><th>Memory</th><th>Latency</th></tr></thead>
<tbody>${workers.map((w) => `<tr><td>${w.label}</td><td>${w.cpu}%</td><td>${w.memory}%</td><td>${w.latency_ms}ms</td></tr>`).join("")}</tbody></table>
<h2>Error Budget</h2>
<p>Budget remaining: <strong>0.0015%</strong> · Allowable failures/month: <strong>44</strong> · Failures this month: <strong>12</strong></p>
<h2>Trust Scores</h2>
<table><thead><tr><th>Worker</th><th>Score</th></tr></thead>
<tbody>${workers.map((w) => `<tr><td>${w.label}</td><td class="${w.cpu > 40 ? 'yellow' : 'green'}">${(0.85 + Math.random() * 0.15).toFixed(3)}</td></tr>`).join("")}</tbody></table>
<div class="meta">NEXUS-RUBYKZ Edge Glow · Confidential</div>
</body></html>`;

  return new NextResponse(html, {
    headers: {
      "Content-Type": "text/html",
      "Content-Disposition": "attachment; filename=nexus-rubykz-report.html",
    },
  });
}
