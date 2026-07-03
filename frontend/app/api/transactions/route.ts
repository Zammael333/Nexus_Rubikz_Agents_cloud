import { NextResponse } from "next/server";

const TXNS = Array.from({ length: 100 }, (_, i) => ({
  id: `txn-${String(i).padStart(6, "0")}`,
  uuid: `550e8400-e29b-41d4-a716-44665544${String(i + 50).padStart(4, "0")}`,
  sku: `SKU-${String(10001 + Math.floor(Math.random() * 8)).padStart(5, "0")}`,
  action: ["lock", "unlock", "reserve", "release", "transfer"][Math.floor(Math.random() * 5)],
  quantity: Math.floor(Math.random() * 10) + 1,
  status: ["committed", "pending", "failed", "retrying"][Math.floor(Math.random() * 4)],
  timestamp: new Date(Date.now() - i * 120000).toISOString(),
  retry_count: Math.floor(Math.random() * 3),
  worker: ["inventory", "scorpion", "reconciliation", "twin"][Math.floor(Math.random() * 4)],
}));

export async function GET(request: Request) {
  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  const limit = Math.min(Number(url.searchParams.get("limit")) || 30, 100);

  let filtered = TXNS;
  if (status && status !== "ALL") filtered = filtered.filter((t) => t.status === status);

  return NextResponse.json({ transactions: filtered.slice(0, limit), total: filtered.length });
}
