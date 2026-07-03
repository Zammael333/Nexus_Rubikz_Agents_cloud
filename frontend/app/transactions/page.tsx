"use client";

import { useEffect, useState, useCallback } from "react";

interface Transaction {
  id: string;
  uuid: string;
  sku: string;
  action: string;
  quantity: number;
  status: string;
  timestamp: string;
  retry_count: number;
  worker: string;
}

const STATUS_COLORS: Record<string, string> = {
  committed: "bg-edge-green/20 text-edge-green border-edge-green/30",
  pending: "bg-edge-yellow/20 text-edge-yellow border-edge-yellow/30",
  failed: "bg-edge-red/20 text-edge-red border-edge-red/30",
  retrying: "bg-edge-orange/20 text-edge-orange border-edge-orange/30",
};

export default function TransactionsPage() {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  const fetchTxns = useCallback(async (status: string) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (status !== "ALL") params.set("status", status);
    const res = await fetch(`/api/transactions?${params}`);
    const data = await res.json();
    setTxns(data.transactions);
    setTotal(data.total);
    setLoading(false);
  }, []);

  useEffect(() => { fetchTxns("ALL"); }, [fetchTxns]);

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Transactions</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">History with UUID, ACID status, retries</p>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <span className="text-[10px] text-nexus-muted uppercase tracking-wider">Status:</span>
        {["ALL", "committed", "pending", "failed", "retrying"].map((s) => (
          <button
            key={s}
            onClick={() => { setFilter(s); fetchTxns(s); }}
            className={`text-[10px] uppercase tracking-wider px-3 py-1 rounded border transition-colors ${filter === s ? STATUS_COLORS[s] || "bg-nexus-surface text-nexus-text border-nexus-border" : "border-nexus-border text-nexus-muted hover:text-nexus-text"}`}
          >
            {s}
          </button>
        ))}
        <span className="text-[10px] text-nexus-muted ml-auto">{total} transactions</span>
      </div>

      {loading ? (
        <div className="text-xs text-nexus-muted text-center py-12">Loading transactions...</div>
      ) : (
        <div className="border border-nexus-border rounded-lg overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="bg-nexus-surface border-b border-nexus-border">
                <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">UUID</th>
                <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">SKU</th>
                <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Action</th>
                <th className="text-right p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Qty</th>
                <th className="text-center p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Status</th>
                <th className="text-right p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Retries</th>
                <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Worker</th>
                <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody>
              {txns.map((tx) => (
                <tr key={tx.id} className="border-b border-nexus-border/50 hover:bg-nexus-surface/50 transition-colors">
                  <td className="p-3 text-nexus-muted text-[10px]" title={tx.uuid}>{tx.uuid.slice(0, 19)}…</td>
                  <td className="p-3 text-nexus-text">{tx.sku}</td>
                  <td className="p-3 text-nexus-text">{tx.action}</td>
                  <td className="p-3 text-right text-nexus-text">{tx.quantity}</td>
                  <td className="p-3 text-center">
                    <span className={`text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border ${STATUS_COLORS[tx.status]}`}>
                      {tx.status}
                    </span>
                  </td>
                  <td className="p-3 text-right text-nexus-muted">{tx.retry_count}</td>
                  <td className="p-3 text-nexus-text">{tx.worker}</td>
                  <td className="p-3 text-nexus-muted text-[10px]">{new Date(tx.timestamp).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
