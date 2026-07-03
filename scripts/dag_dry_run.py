#!/usr/bin/env python3
"""DAG Orchestrator Dry-Run: OTel-layer cold simulation.

Builds representative DAG topologies, exercises the orchestrator in
local-only mode (no A2A transport), and measures execution-plan latency
to confirm the OTel instrumentation layers do not degrade the 99.973 % SLO.

Exit codes:
    0  — all latency budgets met
    1  — topological-sort or execution-plan latency exceeds SLO budget
    2  — unexpected error during simulation
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import sys
import time

# ---------------------------------------------------------------------------
# Path setup — allow direct execution without package install
# ---------------------------------------------------------------------------

import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.dag.orchestrator import DAGGraph, DAGNode, DAGOrchestrator  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SLO_PERCENTILE_TARGET = 99.973  # %
SLO_PERCENTILE_FRAC = SLO_PERCENTILE_TARGET / 100.0  # 0.99973

# Latency budgets (wall-clock milliseconds) — vastly below the 300 s per-node
# timeout so any regression is detectable.
BUDGET_TOPOSORT_MS = 5.0       # single topological_sort call
BUDGET_EXECUTION_PLAN_MS = 10.0  # get_execution_plan_by_level
BUDGET_FULL_EXECUTION_MS = 200.0  # full async execute() in local mode (no A2A)

WARMUP_RUNS = 3
BENCH_RUNS = 20

logger = logging.getLogger("dag_dry_run")


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _build_flat_graph(node_count: int) -> DAGGraph:
    """A DAG with no dependencies — all nodes execute in parallel."""
    g = DAGGraph()
    for i in range(node_count):
        g.add_node(DAGNode(worker_id=f"worker_{i}"))
    return g


def _build_chain_graph(length: int) -> DAGGraph:
    """A linear chain — each node depends on the previous one."""
    g = DAGGraph()
    g.add_node(DAGNode(worker_id="worker_0"))
    for i in range(1, length):
        g.add_node(DAGNode(worker_id=f"worker_{i}", depends_on=[f"worker_{i-1}"]))
    return g


def _build_multi_level_graph(levels: int, fan_out: int) -> DAGGraph:
    """Wide DAG: each level fans out to *fan_out* children."""
    g = DAGGraph()
    prev_level: list[str] = []
    for level in range(levels):
        cur_level: list[str] = []
        for f in range(fan_out):
            wid = f"L{level}_N{f}"
            deps = list(prev_level) if prev_level else []
            g.add_node(DAGNode(worker_id=wid, depends_on=deps))
            cur_level.append(wid)
        prev_level = cur_level
    return g


# ---------------------------------------------------------------------------
# Benchmark: topological sort & execution plan generation
# ---------------------------------------------------------------------------


async def bench_static_planning(
    graph: DAGGraph,
    label: str,
) -> tuple[float, float, dict[str, float]]:
    """Benchmark topological_sort and get_execution_plan_by_level.

    Returns (avg_topo_ms, avg_plan_ms, all_latencies_dict).
    """
    orchestrator = DAGOrchestrator(graph=graph)
    topo_latencies: list[float] = []
    plan_latencies: list[float] = []

    # Warmup
    for _ in range(WARMUP_RUNS):
        orchestrator.get_execution_plan()
        orchestrator.get_execution_plan_by_level()

    for _ in range(BENCH_RUNS):
        t0 = time.perf_counter()
        plan = orchestrator.get_execution_plan()
        topo_latencies.append(_elapsed_ms(t0))

        t0 = time.perf_counter()
        by_level = orchestrator.get_execution_plan_by_level()
        plan_latencies.append(_elapsed_ms(t0))

    avg_topo = statistics.mean(topo_latencies)
    avg_plan = statistics.mean(plan_latencies)

    p99_973_topo = _percentile(topo_latencies, SLO_PERCENTILE_FRAC)
    p99_973_plan = _percentile(plan_latencies, SLO_PERCENTILE_FRAC)

    logger.info(
        "  %-28s  topo=%.4fms(p99.973=%.4f)  plan=%.4fms(p99.973=%.4f)  nodes=%d",
        label,
        avg_topo,
        p99_973_topo,
        avg_plan,
        p99_973_plan,
        len(graph.nodes),
    )

    return avg_topo, avg_plan, {
        "label": label,
        "node_count": len(graph.nodes),
        "topo_avg_ms": avg_topo,
        "topo_p99_973_ms": p99_973_topo,
        "plan_avg_ms": avg_plan,
        "plan_p99_973_ms": p99_973_plan,
    }


# ---------------------------------------------------------------------------
# Benchmark: full DAG execution (cold, local-only — no A2A)
# ---------------------------------------------------------------------------


async def bench_full_execution(
    graph: DAGGraph,
    label: str,
) -> dict[str, float]:
    """Benchmark the full orchestrator.execute() loop without A2A transport.

    Internal node execution becomes a near-zero-cost state transition
    (no-A2A path → marks COMPLETED instantly), so this measures the
    orchestrator's dispatch overhead exclusively.
    """
    exec_latencies: list[float] = []

    for _ in range(WARMUP_RUNS):
        orch = DAGOrchestrator(graph=graph)
        g2 = DAGGraph()
        for _, n in graph.nodes.items():
            g2.add_node(
                DAGNode(worker_id=n.worker_id, depends_on=list(n.depends_on))
            )
        orch.graph = g2
        await orch.execute(stop_on_failure=False)

    for _ in range(BENCH_RUNS):
        orch = DAGOrchestrator(graph=graph)
        g2 = DAGGraph()
        for _, n in graph.nodes.items():
            g2.add_node(
                DAGNode(worker_id=n.worker_id, depends_on=list(n.depends_on))
            )
        orch.graph = g2
        t0 = time.perf_counter()
        summary = await orch.execute(stop_on_failure=False)
        exec_latencies.append(_elapsed_ms(t0))

    avg_exec = statistics.mean(exec_latencies)
    p99_973_exec = _percentile(exec_latencies, SLO_PERCENTILE_FRAC)

    logger.info(
        "  %-28s  exec=%.4fms(p99.973=%.4f)  nodes=%d  success=%s",
        label,
        avg_exec,
        p99_973_exec,
        len(graph.nodes),
        summary.get("success"),
    )

    return {
        "label": label,
        "node_count": len(graph.nodes),
        "exec_avg_ms": avg_exec,
        "exec_p99_973_ms": p99_973_exec,
    }


def _percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


# ---------------------------------------------------------------------------
# SLO validation
# ---------------------------------------------------------------------------


def _validate_slo(
    results: list[dict[str, float]],
    budgets: dict[str, float],
) -> bool:
    ok = True
    for r in results:
        for metric, budget_ms in budgets.items():
            val = r.get(metric)
            if val is not None and val > budget_ms:
                logger.error(
                    "  FAIL  %-20s %s=%.4fms > budget=%.4fms",
                    r.get("label", ""),
                    metric,
                    val,
                    budget_ms,
                )
                ok = False
    if ok:
        logger.info("  All latency budgets satisfied.")
    return ok


# ===========================================================================
# Main
# ===========================================================================


async def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("=" * 72)
    logger.info("DAG Orchestrator Dry-Run — OTel Latency Simulation")
    logger.info("SLO target: %.3f %%", SLO_PERCENTILE_TARGET)
    logger.info("Budgets: topo≤%.1fms  plan≤%.1fms  exec≤%.1fms", BUDGET_TOPOSORT_MS, BUDGET_EXECUTION_PLAN_MS, BUDGET_FULL_EXECUTION_MS)
    logger.info("=" * 72)

    topologies: list[tuple[str, DAGGraph]] = [
        ("flat-10", _build_flat_graph(10)),
        ("flat-100", _build_flat_graph(100)),
        ("chain-10", _build_chain_graph(10)),
        ("chain-50", _build_chain_graph(50)),
        ("multi-L5-F4", _build_multi_level_graph(5, 4)),
        ("multi-L10-F8", _build_multi_level_graph(10, 8)),
    ]

    static_results: list[dict[str, float]] = []

    logger.info("\n--- Static analysis (topological sort + plan) ---")
    for label, graph in topologies:
        _, _, info = await bench_static_planning(graph, label)
        static_results.append(info)

    exec_results: list[dict[str, float]] = []

    logger.info("\n--- Full execution (local-only, no A2A) ---")
    # Only run full execution for smaller topologies; the 640-node DAG
    # spawns 640 sequential dispatch entries.
    small_topos = [(label_, graph_) for label_, graph_ in topologies if len(graph_.nodes) <= 100]
    for label, graph in small_topos:
        info = await bench_full_execution(graph, label)
        exec_results.append(info)

    logger.info("\n--- SLO verification ---")
    slo_ok = _validate_slo(static_results, {
        "topo_avg_ms": BUDGET_TOPOSORT_MS,
        "topo_p99_973_ms": BUDGET_TOPOSORT_MS * 1.5,
        "plan_avg_ms": BUDGET_EXECUTION_PLAN_MS,
        "plan_p99_973_ms": BUDGET_EXECUTION_PLAN_MS * 1.5,
    })
    exec_ok = _validate_slo(exec_results, {
        "exec_avg_ms": BUDGET_FULL_EXECUTION_MS,
        "exec_p99_973_ms": BUDGET_FULL_EXECUTION_MS * 2.0,
    })

    logger.info("\n" + "=" * 72)
    if slo_ok and exec_ok:
        logger.info("RESULT: PASS — All latency budgets within SLO %.3f %%", SLO_PERCENTILE_TARGET)
    else:
        logger.error("RESULT: FAIL — Latency budgets exceeded. Review OTel overhead.")
    logger.info("=" * 72)

    return 0 if (slo_ok and exec_ok) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
