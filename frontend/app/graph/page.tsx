"use client";

import { useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Pulse } from "@/components/EdgeGlow";

interface WorkerData {
  id: string;
  label: string;
  status: string;
  trust_score: number;
  pulse: Pulse;
}

type FlowNode = Node<Record<string, unknown>, "worker">;
type FlowEdge = Edge;

const NODE_COLORS: Record<Pulse, string> = {
  green: "border-edge-green bg-edge-green/10 text-edge-green",
  yellow: "border-edge-yellow bg-edge-yellow/10 text-edge-yellow",
  orange: "border-edge-orange bg-edge-orange/10 text-edge-orange",
  red: "border-edge-red bg-edge-red/10 text-edge-red",
};

function WorkerNode({ data }: { data: Record<string, unknown> }) {
  const w = data as unknown as WorkerData;
  return (
    <div className={`px-4 py-3 rounded border-2 font-mono text-xs min-w-[140px] ${NODE_COLORS[w.pulse]}`}>
      <div className="font-bold tracking-wider uppercase">{w.label}</div>
      <div className="flex justify-between mt-1 opacity-70">
        <span>{w.status}</span>
        <span>{w.trust_score.toFixed(2)}</span>
      </div>
    </div>
  );
}

const nodeTypes = { worker: WorkerNode };

export default function GraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<FlowEdge>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/graph")
      .then((r) => r.json())
      .then((data) => {
        const flowNodes: FlowNode[] = data.workers.map((w: Record<string, unknown>, i: number) => ({
          id: w.id as string,
          type: "worker",
          position: { x: 150 + (i % 4) * 200, y: 80 + Math.floor(i / 4) * 140 },
          data: w,
        }));
        const flowEdges: FlowEdge[] = data.edges.map((e: Record<string, unknown>, i: number) => ({
          id: `e-${i}`,
          source: e.source,
          target: e.target,
          label: e.label,
          animated: true,
          style: { stroke: "#1e3a5f", strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#1e3a5f" },
          labelStyle: { fill: "#8888aa", fontSize: 9, fontFamily: "JetBrains Mono, monospace" },
        }));
        setNodes(flowNodes);
        setEdges(flowEdges);
        setLoading(false);
      });
  }, [setNodes, setEdges]);

  return (
    <div className="h-full">
      <div className="mb-4">
        <h1 className="text-lg font-bold tracking-widest uppercase text-nexus-text">Worker Graph</h1>
        <p className="text-[10px] text-nexus-muted tracking-wider mt-1">Interactive graph of atomic workers and their A2A / DAG connections</p>
      </div>
      {loading ? (
        <div className="flex items-center justify-center h-[70vh] text-nexus-muted text-xs tracking-wider">Loading graph...</div>
      ) : (
        <div className="h-[70vh] border border-nexus-border rounded-lg overflow-hidden" style={{ background: "#0a0a1a" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color="#1e1e3f" gap={20} />
            <Controls className="bg-nexus-surface border border-nexus-border rounded" />
            <MiniMap
              nodeColor={() => "#1e3a5f"}
              maskColor="#0a0a1a"
              className="border border-nexus-border rounded"
            />
          </ReactFlow>
        </div>
      )}
    </div>
  );
}
