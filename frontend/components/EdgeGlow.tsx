export type Pulse = "green" | "yellow" | "orange" | "red";

const PULSE_COLORS: Record<Pulse, string> = {
  green: "bg-edge-green shadow-[0_0_12px_rgba(0,255,136,0.5)]",
  yellow: "bg-edge-yellow shadow-[0_0_12px_rgba(255,204,0,0.5)]",
  orange: "bg-edge-orange shadow-[0_0_12px_rgba(255,102,0,0.5)]",
  red: "bg-edge-red shadow-[0_0_12px_rgba(255,0,51,0.5)]",
};

const TEXT_COLORS: Record<Pulse, string> = {
  green: "text-edge-green",
  yellow: "text-edge-yellow",
  orange: "text-edge-orange",
  red: "text-edge-red",
};

export function EdgeGlowDot({ pulse, size = "md" }: { pulse: Pulse; size?: "sm" | "md" | "lg" }) {
  const sizeClass = size === "sm" ? "w-3 h-3" : size === "lg" ? "w-8 h-8" : "w-5 h-5";
  return <span className={`inline-block rounded-full ${sizeClass} ${PULSE_COLORS[pulse]} transition-all duration-500`} />;
}

export function EdgeGlowLabel({ pulse }: { pulse: Pulse }) {
  return <span className={`text-xs font-semibold uppercase tracking-wider ${TEXT_COLORS[pulse]}`}>{pulse}</span>;
}

export function pulseFromSlo(slo: number): Pulse {
  if (slo >= 99.997) return "green";
  if (slo >= 99.99) return "yellow";
  if (slo >= 99.97) return "orange";
  return "red";
}
