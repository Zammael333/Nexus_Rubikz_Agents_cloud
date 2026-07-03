from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DAGNodeStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    worker_id: str
    depends_on: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: DAGNodeStatus = DAGNodeStatus.PENDING
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "depends_on": list(self.depends_on),
            "metadata": dict(self.metadata),
            "status": self.status.value,
            "error": self.error,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DAGNode:
        return DAGNode(
            worker_id=data["worker_id"],
            depends_on=list(data.get("depends_on", [])),
            metadata=dict(data.get("metadata", {})),
            status=DAGNodeStatus(data.get("status", "pending")),
            error=data.get("error", ""),
        )


@dataclass
class DAGGraph:
    nodes: dict[str, DAGNode] = field(default_factory=dict)

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.worker_id] = node

    def remove_node(self, worker_id: str) -> None:
        self.nodes.pop(worker_id, None)
        for node in self.nodes.values():
            if worker_id in node.depends_on:
                node.depends_on.remove(worker_id)

    def add_dependency(self, worker_id: str, depends_on: str) -> None:
        if worker_id not in self.nodes:
            self.nodes[worker_id] = DAGNode(worker_id=worker_id)
        if depends_on not in self.nodes:
            self.nodes[depends_on] = DAGNode(worker_id=depends_on)
        if depends_on not in self.nodes[worker_id].depends_on:
            self.nodes[worker_id].depends_on.append(depends_on)

    def remove_dependency(self, worker_id: str, depends_on: str) -> None:
        node = self.nodes.get(worker_id)
        if node and depends_on in node.depends_on:
            node.depends_on.remove(depends_on)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for nid, node in self.nodes.items():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    errors.append(f"Node '{nid}' depends on missing node '{dep}'")
                if dep == nid:
                    errors.append(f"Node '{nid}' depends on itself")
        cycle = self._find_cycle()
        if cycle:
            errors.append(f"Cycle detected: {' → '.join(cycle)}")
        return errors

    def _find_cycle(self) -> list[str]:
        visiting: set[str] = set()
        visited: set[str] = set()
        path: list[str] = []

        def dfs(nid: str) -> list[str] | None:
            visiting.add(nid)
            path.append(nid)
            node = self.nodes.get(nid)
            if node:
                for dep in node.depends_on:
                    if dep in visiting:
                        cycle_start = path.index(dep)
                        return [*path[cycle_start:], dep]
                    if dep not in visited:
                        result = dfs(dep)
                        if result:
                            return result
            path.pop()
            visiting.discard(nid)
            visited.add(nid)
            return None

        for nid in list(self.nodes.keys()):
            if nid not in visited:
                result = dfs(nid)
                if result:
                    return result
        return []

    def topological_sort(self) -> list[str]:
        errors = self.validate()
        if errors:
            raise ValueError(f"DAG validation failed: {'; '.join(errors)}")
        in_degree: dict[str, int] = {}
        adjacency: dict[str, list[str]] = defaultdict(list)
        for nid in self.nodes:
            in_degree[nid] = 0
        for nid, node in self.nodes.items():
            for dep in node.depends_on:
                adjacency.setdefault(dep, []).append(nid)
                in_degree[nid] = in_degree.get(nid, 0) + 1
        queue: deque[str] = deque()
        for nid, degree in in_degree.items():
            if degree == 0:
                queue.append(nid)
        result: list[str] = []
        while queue:
            nid = queue.popleft()
            result.append(nid)
            for neighbor in adjacency.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(result) != len(self.nodes):
            raise ValueError("DAG contains a cycle")
        return result

    def get_upstream(self, worker_id: str) -> list[DAGNode]:
        node = self.nodes.get(worker_id)
        if not node:
            return []
        return [self.nodes[d] for d in node.depends_on if d in self.nodes]

    def get_downstream(self, worker_id: str) -> list[DAGNode]:
        return [n for n in self.nodes.values() if worker_id in n.depends_on]

    def ready_nodes(self, completed: set[str]) -> list[DAGNode]:
        ready: list[DAGNode] = []
        for node in self.nodes.values():
            if node.worker_id in completed:
                continue
            if node.status not in (DAGNodeStatus.PENDING, DAGNodeStatus.READY):
                continue
            deps_met = all(d in completed for d in node.depends_on)
            if deps_met:
                ready.append(node)
        return ready

    def reset_status(self) -> None:
        for node in self.nodes.values():
            node.status = DAGNodeStatus.PENDING
            node.error = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {wid: node.to_dict() for wid, node in self.nodes.items()},
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> DAGGraph:
        graph = DAGGraph()
        for wid, node_data in data.get("nodes", {}).items():
            graph.nodes[wid] = DAGNode.from_dict(node_data)
        return graph


class DAGOrchestrator:
    def __init__(
        self,
        graph: DAGGraph | None = None,
        a2a_protocol=None,
        trust_scorer=None,
        execution_timeout: float | None = None,
    ):
        self._graph = graph or DAGGraph()
        self._a2a = a2a_protocol
        self._trust_scorer = trust_scorer
        from app.config import settings
        self._execution_timeout = execution_timeout if execution_timeout is not None else settings.dag_global_timeout
        self._execution_history: list[dict[str, Any]] = []
        self._running = False

    @property
    def graph(self) -> DAGGraph:
        return self._graph

    @graph.setter
    def graph(self, g: DAGGraph) -> None:
        self._graph = g

    def get_execution_plan(self) -> list[str]:
        return self._graph.topological_sort()

    def get_execution_plan_by_level(self) -> list[list[str]]:
        order = self._graph.topological_sort()
        level_map: dict[str, int] = {}
        for nid in order:
            node = self._graph.nodes.get(nid)
            if not node:
                level_map[nid] = 0
                continue
            if not node.depends_on:
                level_map[nid] = 0
            else:
                level_map[nid] = max(level_map.get(d, 0) for d in node.depends_on) + 1
        levels: list[list[str]] = []
        for nid in order:
            lvl = level_map[nid]
            while len(levels) <= lvl:
                levels.append([])
            levels[lvl].append(nid)
        return levels

    def estimate_trust_reliability(self, worker_id: str) -> float:
        if not self._trust_scorer:
            return 1.0
        report = self._trust_scorer.get_latest(worker_id)
        if report is None:
            return 1.0
        return report.overall_score

    async def execute_node(
        self,
        worker_id: str,
        action: str = "dag_execute",
        payload: dict[str, Any] | None = None,
    ) -> bool:
        node = self._graph.nodes.get(worker_id)
        if node is None:
            logger.warning(f"[DAG] Node '{worker_id}' not found in graph")
            return False

        reliability = self.estimate_trust_reliability(worker_id)
        if reliability < 0.3:
            logger.warning(
                f"[DAG] Skipping '{worker_id}' — trust {reliability:.2f} < 0.3"
            )
            node.status = DAGNodeStatus.SKIPPED
            node.error = f"Trust too low: {reliability:.2f}"
            self._execution_history.append(
                {
                    "worker_id": worker_id,
                    "status": "skipped",
                    "reason": node.error,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            return False

        if not self._a2a:
            logger.warning(
                f"[DAG] No A2A protocol set, marking '{worker_id}' as COMPLETED"
            )
            node.status = DAGNodeStatus.COMPLETED
            self._execution_history.append(
                {
                    "worker_id": worker_id,
                    "status": "completed",
                    "reason": "No A2A (local mode)",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            return True

        node.status = DAGNodeStatus.RUNNING
        try:
            result = await self._a2a.send_request(
                target_worker=worker_id,
                action=action,
                payload=payload or {},
                timeout=self._execution_timeout,
            )
            if result.success:
                node.status = DAGNodeStatus.COMPLETED
                self._execution_history.append(
                    {
                        "worker_id": worker_id,
                        "status": "completed",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                return True
            else:
                node.status = DAGNodeStatus.FAILED
                node.error = result.error
                self._execution_history.append(
                    {
                        "worker_id": worker_id,
                        "status": "failed",
                        "error": result.error,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                return False
        except Exception as e:
            node.status = DAGNodeStatus.FAILED
            node.error = str(e)
            self._execution_history.append(
                {
                    "worker_id": worker_id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            return False

    async def execute(
        self,
        action: str = "dag_execute",
        payload: dict[str, Any] | None = None,
        stop_on_failure: bool = True,
    ) -> dict[str, Any]:
        if self._running:
            raise RuntimeError("DAGOrchestrator is already running")
        self._running = True
        self._graph.reset_status()

        plan = self.get_execution_plan()
        logger.info(f"[DAG] Execution plan: {' → '.join(plan)}")

        completed: set[str] = set()
        failed: set[str] = set()
        skipped: set[str] = set()
        start_time = datetime.now(UTC)

        while len(completed) + len(failed) + len(skipped) < len(plan):
            ready = self._graph.ready_nodes(completed)
            if not ready:
                remaining = set(self._graph.nodes) - completed - failed - skipped
                if remaining:
                    remaining_no_new_deps = [
                        r
                        for r in remaining
                        if all(
                            d in completed or d in failed or d in skipped
                            for d in self._graph.nodes[r].depends_on
                        )
                    ]
                    if remaining_no_new_deps and not ready:
                        for wid in remaining_no_new_deps:
                            node = self._graph.nodes[wid]
                            if node.status in (
                                DAGNodeStatus.PENDING,
                                DAGNodeStatus.READY,
                            ):
                                node.status = DAGNodeStatus.FAILED
                                node.error = "Upstream dependencies failed"
                                failed.add(wid)
                                self._execution_history.append(
                                    {
                                        "worker_id": wid,
                                        "status": "failed",
                                        "error": "Upstream dependencies failed",
                                        "timestamp": datetime.now(UTC).isoformat(),
                                    }
                                )
                        continue
                break

            tasks = [
                self.execute_node(node.worker_id, action, payload) for node in ready
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for node, result in zip(ready, results, strict=True):
                if isinstance(result, Exception):
                    node.status = DAGNodeStatus.FAILED
                    node.error = str(result)
                    failed.add(node.worker_id)
                    self._execution_history.append(
                        {
                            "worker_id": node.worker_id,
                            "status": "failed",
                            "error": str(result),
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                elif result is True:
                    completed.add(node.worker_id)
                elif result is False and node.status == DAGNodeStatus.SKIPPED:
                    skipped.add(node.worker_id)
                else:
                    failed.add(node.worker_id)

            if stop_on_failure and failed:
                logger.warning(f"[DAG] Stopping due to failures: {failed}")
                for wid in plan:
                    node = self._graph.nodes.get(wid)
                    if node and node.status == DAGNodeStatus.PENDING:
                        node.status = DAGNodeStatus.SKIPPED
                        skipped.add(wid)
                break

        end_time = datetime.now(UTC)
        self._running = False

        summary = {
            "success": len(failed) == 0 and len(skipped) == 0,
            "completed": [wid for wid in plan if wid in completed],
            "failed": [wid for wid in plan if wid in failed],
            "skipped": [wid for wid in plan if wid in skipped],
            "total": len(plan),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
        logger.info(
            f"[DAG] Execution finished — "
            f"{len(completed)} ok, {len(failed)} failed, {len(skipped)} skipped"
        )
        return summary

    @property
    def execution_history(self) -> list[dict[str, Any]]:
        return list(self._execution_history)

    @property
    def running(self) -> bool:
        return self._running

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph": self._graph.to_dict(),
            "execution_history": list(self._execution_history),
            "running": self._running,
        }
