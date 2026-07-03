"use client";

interface BudgetControlProps {
  onFreeze: () => void;
  onThaw: () => void;
  frozen: boolean;
}

export default function BudgetControl({ onFreeze, onThaw, frozen }: BudgetControlProps) {
  const budgetUsed = 0.0027;
  const budgetTotal = 100;
  const budgetPercent = (budgetUsed / budgetTotal) * 100;

  return (
    <div className="bg-nexus-surface border border-nexus-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs font-bold text-nexus-text uppercase tracking-wider">
            Error Budget
          </div>
          <div className="text-[10px] text-nexus-muted tracking-wider mt-0.5">
            {frozen ? "FROZEN" : "ACTIVE"}
          </div>
        </div>
        <button
          onClick={frozen ? onThaw : onFreeze}
          className={`text-[10px] uppercase tracking-wider px-3 py-1.5 rounded border transition-colors ${
            frozen
              ? "bg-edge-green/20 text-edge-green border-edge-green/30 hover:bg-edge-green/30"
              : "bg-edge-yellow/20 text-edge-yellow border-edge-yellow/30 hover:bg-edge-yellow/30"
          }`}
        >
          {frozen ? "Thaw" : "Freeze"}
        </button>
      </div>

      <div className="w-full h-2 bg-nexus-bg rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.min(budgetPercent, 100)}%`,
            background: budgetPercent > 80 ? "#ff6600" : budgetPercent > 50 ? "#ffcc00" : "#00ff88",
          }}
        />
      </div>

      <div className="flex justify-between mt-1">
        <span className="text-[9px] text-nexus-muted">
          {budgetUsed.toFixed(4)}% used
        </span>
        <span className="text-[9px] text-nexus-muted">
          {frozen ? "—" : "0.0027% remaining"}
        </span>
      </div>
    </div>
  );
}
