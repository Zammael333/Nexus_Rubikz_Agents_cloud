"use client";

import { useEffect, useState } from "react";
import { EdgeGlowDot, EdgeGlowLabel, type Pulse } from "@/components/EdgeGlow";

interface SKU {
  sku: string;
  name: string;
  quantity: number;
  locked: boolean;
  lock_owner: string | null;
  lock_held_since: string | null;
}

export default function InventoryPage() {
  const [skus, setSkus] = useState<SKU[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newQty, setNewQty] = useState("10");

  const fetchSkus = () => fetch("/api/inventory").then((r) => r.json()).then((d) => { setSkus(d.skus); setLoading(false); });

  useEffect(() => { fetchSkus(); }, []);

  const toggleLock = async (sku: string, lock: boolean) => {
    await fetch("/api/inventory", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: lock ? "lock" : "unlock", sku }) });
    fetchSkus();
  };

  const createSku = async () => {
    if (!newName.trim()) return;
    await fetch("/api/inventory", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "create", name: newName, quantity: Number(newQty) }) });
    setNewName("");
    setNewQty("10");
    setShowCreate(false);
    fetchSkus();
  };

  if (loading) return <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs">Loading inventory...</div>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Inventory</h1>
          <p className="text-[10px] text-nexus-muted tracking-wider mt-1">SKU catalog with active lock visualization</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-1.5 bg-edge-green/20 text-edge-green text-[10px] uppercase tracking-wider rounded border border-edge-green/30 hover:bg-edge-green/30 transition-colors">+ New SKU</button>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-nexus-surface border border-nexus-border rounded-lg p-6 w-96" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-sm font-bold text-nexus-text uppercase tracking-wider mb-4">Create SKU</h2>
            <label className="text-[10px] text-nexus-muted uppercase tracking-wider block mb-1">Name</label>
            <input value={newName} onChange={(e) => setNewName(e.target.value)} className="w-full bg-nexus-bg border border-nexus-border rounded px-3 py-2 text-xs text-nexus-text font-mono mb-3 outline-none" placeholder="Widget Name" />
            <label className="text-[10px] text-nexus-muted uppercase tracking-wider block mb-1">Quantity</label>
            <input type="number" value={newQty} onChange={(e) => setNewQty(e.target.value)} className="w-full bg-nexus-bg border border-nexus-border rounded px-3 py-2 text-xs text-nexus-text font-mono mb-4 outline-none" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowCreate(false)} className="px-4 py-1.5 text-[10px] text-nexus-muted uppercase tracking-wider border border-nexus-border rounded">Cancel</button>
              <button onClick={createSku} className="px-4 py-1.5 bg-edge-green/20 text-edge-green text-[10px] uppercase tracking-wider border border-edge-green/30 rounded">Create</button>
            </div>
          </div>
        </div>
      )}

      <div className="border border-nexus-border rounded-lg overflow-hidden">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="bg-nexus-surface border-b border-nexus-border">
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">SKU</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Name</th>
              <th className="text-right p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Qty</th>
              <th className="text-center p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Lock</th>
              <th className="text-left p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Owner</th>
              <th className="text-center p-3 text-nexus-muted text-[10px] uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody>
            {skus.map((sku) => {
              const pulse: Pulse = sku.locked ? "yellow" : sku.quantity === 0 ? "red" : "green";
              return (
                <tr key={sku.sku} className="border-b border-nexus-border/50 hover:bg-nexus-surface/50 transition-colors">
                  <td className="p-3 text-nexus-text">{sku.sku}</td>
                  <td className="p-3 text-nexus-text">{sku.name}</td>
                  <td className={`p-3 text-right ${sku.quantity === 0 ? "text-edge-red" : "text-nexus-text"}`}>{sku.quantity}</td>
                  <td className="p-3 text-center"><EdgeGlowDot pulse={pulse} size="sm" /></td>
                  <td className="p-3 text-nexus-muted">{sku.lock_owner ?? "—"}</td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => toggleLock(sku.sku, !sku.locked)}
                      className={`text-[10px] uppercase tracking-wider px-3 py-1 rounded border ${sku.locked ? "text-edge-yellow border-edge-yellow/30 bg-edge-yellow/10" : "text-edge-green border-edge-green/30 bg-edge-green/10"} hover:opacity-80 transition-opacity`}
                    >
                      {sku.locked ? "Unlock" : "Lock"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
