"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Pulse", icon: "◉" },
  { href: "/graph", label: "Graph", icon: "◎" },
  { href: "/twin", label: "Digital Twin", icon: "◆" },
  { href: "/events", label: "Events", icon: "≡" },
  { href: "/inventory", label: "Inventory", icon: "☰" },
  { href: "/transactions", label: "Transactions", icon: "⇄" },
  { href: "/health", label: "Health", icon: "♥" },
  { href: "/dead-letter", label: "Dead Letter", icon: "☠" },
  { href: "/vibe-diff", label: "Vibe Diff", icon: "↯" },
  { href: "/spiffe", label: "SPIFFE", icon: "⚔" },
  { href: "/slo", label: "SLO", icon: "◎" },
  { href: "/twin-timeline", label: "Twin Timeline", icon: "◈" },
  { href: "/traces", label: "Traces", icon: "◈" },
  { href: "/heatmap", label: "Heatmap", icon: "▣" },
  { href: "/scans", label: "Scans", icon: "◉" },
  { href: "/trust", label: "Trust", icon: "♦" },
  { href: "/budget", label: "Error Budget", icon: "⊡" },
  { href: "/phoenix-history", label: "Phoenix History", icon: "♻" },
  { href: "/cloud-monitoring", label: "Cloud", icon: "☁" },
  { href: "/alerting", label: "Alerting", icon: "⚡" },
  { href: "/audit-trail", label: "Audit Trail", icon: "📋" },
  { href: "/backups", label: "Backups", icon: "💾" },
  { href: "/compliance", label: "Compliance", icon: "✓" },
  { href: "/cost", label: "Cost", icon: "$" },
  { href: "/incidents", label: "Incidents", icon: "⚠" },
  { href: "/maintenance", label: "Maintenance", icon: "🔧" },
  { href: "/runbooks", label: "Runbooks", icon: "📄" },
  { href: "/secrets", label: "Secrets", icon: "🔑" },
  { href: "/topology", label: "Topology", icon: "🔗" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const nav = (
    <>
      <div className="p-4 border-b border-nexus-border">
        <Link href="/" className="text-sm font-bold tracking-widest uppercase text-nexus-text block" onClick={() => setOpen(false)}>
          NEXUS<span className="text-edge-green">RUBYKZ</span>
        </Link>
        <div className="text-[10px] text-nexus-muted tracking-widest mt-1">Edge Glow · v0.1</div>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 rounded text-xs tracking-wider uppercase transition-all ${
                isActive
                  ? "bg-edge-green/10 text-edge-green border border-edge-green/30"
                  : "text-nexus-muted hover:text-nexus-text hover:bg-nexus-border/50 border border-transparent"
              }`}
            >
              <span className="text-sm">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-nexus-border text-[10px] text-nexus-muted text-center">
        SLO 99.9973% · Error Budget 0.0027%
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="lg:hidden fixed top-3 left-3 z-50 w-9 h-9 flex items-center justify-center bg-nexus-surface border border-nexus-border rounded text-nexus-text text-sm"
        aria-label="Toggle navigation"
      >
        {open ? "✕" : "☰"}
      </button>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex fixed left-0 top-0 bottom-0 w-56 bg-nexus-surface border-r border-nexus-border flex-col z-40">
        {nav}
      </aside>

      {/* Mobile overlay sidebar */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-black/60" />
          <aside className="relative w-64 h-full bg-nexus-surface border-r border-nexus-border flex flex-col" onClick={(e) => e.stopPropagation()}>
            {nav}
          </aside>
        </div>
      )}
    </>
  );
}
