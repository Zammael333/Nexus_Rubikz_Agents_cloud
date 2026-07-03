import { NextResponse } from "next/server";

const TWIN_BASE = process.env.TWIN_API_URL || "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${TWIN_BASE}/api/v1/twin/phoenix-reports`, {
      signal: AbortSignal.timeout(3000),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      workers: {},
      total_workers: 0,
    });
  }
}
