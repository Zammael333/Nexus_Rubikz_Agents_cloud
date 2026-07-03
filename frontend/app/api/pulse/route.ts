import { NextResponse } from "next/server";

const PULSE_CYCLES = ["green", "yellow", "orange", "red"] as const;
type Pulse = (typeof PULSE_CYCLES)[number];

const SLO_TARGET = 99.9973;
const ERROR_BUDGET_TARGET = 0.0027;

let cycleIndex = 0;

export async function GET() {
  cycleIndex = (cycleIndex + 1) % PULSE_CYCLES.length;
  const pulse = PULSE_CYCLES[cycleIndex] as Pulse;

  const slo = {
    nominal_slo: SLO_TARGET,
    error_budget: ERROR_BUDGET_TARGET,
    real_slo: pulse === "green" ? SLO_TARGET : SLO_TARGET - (cycleIndex * 0.001),
    error_budget_remaining: pulse === "green" ? ERROR_BUDGET_TARGET : ERROR_BUDGET_TARGET - (cycleIndex * 0.0001),
    slo_pulse: pulse,
  };

  return NextResponse.json({ pulse, slo });
}
