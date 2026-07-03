import { NextResponse } from "next/server";

interface VibeDiff {
  id: string;
  worker: string;
  proposed_change: string;
  reason: string;
  drift_impact: string;
  submitted_at: string;
  status: "pending" | "approved" | "rejected";
  submitted_by: string;
}

const DIFFS: VibeDiff[] = [
  { id: "vd-001", worker: "inventory", proposed_change: "Increase lock timeout from 30s to 60s", reason: "High latency observed during peak hours", drift_impact: "Low — temporary adjustment within SLO bounds", submitted_at: "2026-06-30T14:00:00Z", status: "pending", submitted_by: "scorpion" },
  { id: "vd-002", worker: "reconciliation", proposed_change: "Disable automatic re-sync for failed batches", reason: "Reconciliation loops detected on stuck batches", drift_impact: "Medium — may increase ledger divergence temporarily", submitted_at: "2026-06-30T12:30:00Z", status: "pending", submitted_by: "watchdog" },
  { id: "vd-003", worker: "phoenix", proposed_change: "Reduce RTO threshold from 2000ms to 1500ms", reason: "Tighter recovery SLA requirement from SLO review", drift_impact: "Low — well within observed recovery times", submitted_at: "2026-06-29T09:00:00Z", status: "approved", submitted_by: "twin" },
  { id: "vd-004", worker: "sat-shield", proposed_change: "Increase DA threshold from 0.01 to 0.02", reason: "False positives during scheduled maintenance windows", drift_impact: "Medium — reduces alert sensitivity", submitted_at: "2026-06-28T16:00:00Z", status: "rejected", submitted_by: "red-team" },
  { id: "vd-005", worker: "sandbox", proposed_change: "Allow network egress from sandbox cages", reason: "New worker needs external API access for validation", drift_impact: "High — breaks sandbox isolation model", submitted_at: "2026-07-01T01:00:00Z", status: "pending", submitted_by: "scorpion" },
];

export async function GET() {
  return NextResponse.json({ diffs: DIFFS });
}
