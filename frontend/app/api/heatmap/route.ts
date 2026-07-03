import { NextResponse } from "next/server";

const WORKERS = ["inventory", "watchdog", "scorpion", "notifier", "phoenix", "budget", "sat-shield", "reconciliation", "twin", "sandbox", "otel", "red-team"];
const METRICS = ["cpu", "memory", "latency", "errors"] as const;
type Metric = typeof METRICS[number];

const HOURS = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, "00")}:00`);

function randVal(base: number, variance: number, metric: Metric): number {
  const v = base + Math.random() * variance - variance / 2;
  if (metric === "latency") return Math.round(Math.max(5, v));
  if (metric === "errors") return Math.round(Math.max(0, v));
  return Math.round(Math.max(1, Math.min(100, v)));
}

function generateHeatmapData() {
  const baseVals: Record<Metric, number> = { cpu: 25, memory: 40, latency: 80, errors: 2 };
  const variance: Record<Metric, number> = { cpu: 40, memory: 35, latency: 150, errors: 5 };
  return HOURS.map((hour) => {
    const cells: Record<string, Record<Metric, number>> = {};
    for (const worker of WORKERS) {
      cells[worker] = {} as Record<Metric, number>;
      for (const metric of METRICS) {
        cells[worker][metric] = randVal(baseVals[metric], variance[metric], metric);
      }
    }
    return { hour, cells };
  });
}

export async function GET() {
  return NextResponse.json({ workers: WORKERS, metrics: METRICS, hours: HOURS, data: generateHeatmapData() });
}
