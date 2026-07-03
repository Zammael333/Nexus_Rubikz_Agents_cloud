import { NextResponse } from "next/server";

const WORKERS = ["inventory", "watchdog", "scorpion", "notifier", "phoenix", "budget", "sat-shield", "reconciliation", "twin", "sandbox", "otel", "red-team"];

function generateHistory() {
  const history: string[] = [];
  for (let day = 30; day >= 0; day--) {
    const d = new Date("2026-07-01T00:00:00Z");
    d.setDate(d.getDate() - day);
    history.push(d.toISOString().split("T")[0]);
  }
  return { dates: history };
}

export async function GET() {
  const { dates } = generateHistory();
  const workers = WORKERS.map((name) => {
    let score = 0.85 + Math.random() * 0.15;
    const values = dates.map(() => {
      score = Math.max(0.5, Math.min(1.0, score + (Math.random() - 0.5) * 0.04));
      return score;
    });
    const maskFailIndex = Math.floor(Math.random() * dates.length);
    values[maskFailIndex] = Math.min(values[maskFailIndex], 0.6);
    return { name, scores: values };
  });
  return NextResponse.json({ dates, workers });
}
