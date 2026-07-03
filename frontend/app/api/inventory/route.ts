import { NextResponse } from "next/server";

interface SKU {
  sku: string;
  name: string;
  quantity: number;
  locked: boolean;
  lock_owner: string | null;
  lock_held_since: string | null;
}

let SKUS: SKU[] = [
  { sku: "SKU-10001", name: "Widget Alpha", quantity: 50, locked: false, lock_owner: null, lock_held_since: null },
  { sku: "SKU-10002", name: "Gadget Beta", quantity: 120, locked: true, lock_owner: "inventory-worker", lock_held_since: "2026-07-01T01:00:00Z" },
  { sku: "SKU-10003", name: "Component Gamma", quantity: 5, locked: true, lock_owner: "scorpion-worker", lock_held_since: "2026-07-01T00:30:00Z" },
  { sku: "SKU-10004", name: "Module Delta", quantity: 200, locked: false, lock_owner: null, lock_held_since: null },
  { sku: "SKU-10005", name: "Assembly Epsilon", quantity: 0, locked: false, lock_owner: null, lock_held_since: null },
  { sku: "SKU-10006", name: "Circuit Zeta", quantity: 75, locked: true, lock_owner: "inventory-worker", lock_held_since: "2026-07-01T02:00:00Z" },
  { sku: "SKU-10007", name: "Sensor Eta", quantity: 30, locked: false, lock_owner: null, lock_held_since: null },
  { sku: "SKU-10008", name: "Actuator Theta", quantity: 15, locked: false, lock_owner: null, lock_held_since: null },
];

export async function GET() {
  return NextResponse.json({ skus: SKUS });
}

export async function POST(request: Request) {
  const body = await request.json();
  if (body.action === "create") {
    const newSku = { sku: `SKU-${String(10009 + Math.floor(Math.random() * 90000)).padStart(5, "0")}`, name: body.name, quantity: body.quantity || 0, locked: false, lock_owner: null, lock_held_since: null };
    SKUS.push(newSku);
    return NextResponse.json({ sku: newSku });
  }
  if (body.action === "lock" || body.action === "unlock") {
    SKUS = SKUS.map((s) => s.sku === body.sku ? { ...s, locked: body.action === "lock", lock_owner: body.action === "lock" ? "manual" : null, lock_held_since: body.action === "lock" ? new Date().toISOString() : null } : s);
    return NextResponse.json({ ok: true });
  }
  return NextResponse.json({ error: "unknown action" }, { status: 400 });
}
