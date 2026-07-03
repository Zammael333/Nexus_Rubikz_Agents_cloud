import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.dag.orchestrator import (
    DAGGraph,
    DAGNode,
    DAGNodeStatus,
    DAGOrchestrator,
)


class TestDAGNode:
    def test_defaults(self):
        node = DAGNode(worker_id="w1")
        assert node.worker_id == "w1"
        assert node.depends_on == []
        assert node.metadata == {}
        assert node.status == DAGNodeStatus.PENDING
        assert node.error == ""

    def test_depends_on(self):
        node = DAGNode(worker_id="w3", depends_on=["w1", "w2"])
        assert node.depends_on == ["w1", "w2"]

    def test_metadata(self):
        node = DAGNode(worker_id="w1", metadata={"role": "scanner"})
        assert node.metadata["role"] == "scanner"

    def test_status_transition(self):
        node = DAGNode(worker_id="w1")
        node.status = DAGNodeStatus.READY
        assert node.status == DAGNodeStatus.READY
        node.status = DAGNodeStatus.RUNNING
        assert node.status == DAGNodeStatus.RUNNING
        node.status = DAGNodeStatus.COMPLETED
        assert node.status == DAGNodeStatus.COMPLETED

    def test_error(self):
        node = DAGNode(worker_id="w1")
        node.status = DAGNodeStatus.FAILED
        node.error = "Something broke"
        assert node.error == "Something broke"

    def test_to_dict(self):
        node = DAGNode(
            worker_id="w3",
            depends_on=["w1", "w2"],
            metadata={"priority": 10},
        )
        d = node.to_dict()
        assert d["worker_id"] == "w3"
        assert d["depends_on"] == ["w1", "w2"]
        assert d["metadata"] == {"priority": 10}
        assert d["status"] == "pending"
        assert d["error"] == ""

    def test_to_dict_failed(self):
        node = DAGNode(worker_id="w1")
        node.status = DAGNodeStatus.FAILED
        node.error = "error msg"
        d = node.to_dict()
        assert d["status"] == "failed"
        assert d["error"] == "error msg"

    def test_from_dict(self):
        data = {
            "worker_id": "w3",
            "depends_on": ["w1"],
            "metadata": {"x": 1},
            "status": "completed",
            "error": "",
        }
        node = DAGNode.from_dict(data)
        assert node.worker_id == "w3"
        assert node.depends_on == ["w1"]
        assert node.metadata == {"x": 1}
        assert node.status == DAGNodeStatus.COMPLETED

    def test_from_dict_defaults(self):
        data = {"worker_id": "w1"}
        node = DAGNode.from_dict(data)
        assert node.worker_id == "w1"
        assert node.depends_on == []
        assert node.metadata == {}
        assert node.status == DAGNodeStatus.PENDING
        assert node.error == ""

    def test_to_dict_round_trip(self):
        original = DAGNode(
            worker_id="w2",
            depends_on=["w1"],
            metadata={"env": "prod"},
        )
        original.status = DAGNodeStatus.COMPLETED
        restored = DAGNode.from_dict(original.to_dict())
        assert restored.worker_id == original.worker_id
        assert restored.depends_on == original.depends_on
        assert restored.metadata == original.metadata
        assert restored.status == original.status
        assert restored.error == original.error


class TestDAGGraph:
    def test_empty(self):
        g = DAGGraph()
        assert g.nodes == {}

    def test_add_node(self):
        g = DAGGraph()
        node = DAGNode(worker_id="w1")
        g.add_node(node)
        assert "w1" in g.nodes

    def test_remove_node(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=[]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.remove_node("w1")
        assert "w1" not in g.nodes
        assert "w2" not in g.nodes["w2"].depends_on

    def test_remove_node_not_found(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.remove_node("nonexistent")
        assert "w1" in g.nodes

    def test_add_dependency(self):
        g = DAGGraph()
        g.add_dependency("w2", "w1")
        assert "w1" in g.nodes
        assert "w2" in g.nodes
        assert g.nodes["w2"].depends_on == ["w1"]

    def test_add_dependency_already_exists(self):
        g = DAGGraph()
        g.add_dependency("w2", "w1")
        g.add_dependency("w2", "w1")
        assert g.nodes["w2"].depends_on == ["w1"]

    def test_remove_dependency(self):
        g = DAGGraph()
        g.add_dependency("w3", "w1")
        g.add_dependency("w3", "w2")
        g.remove_dependency("w3", "w1")
        assert g.nodes["w3"].depends_on == ["w2"]

    def test_remove_dependency_not_found(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.remove_dependency("w1", "nonexistent")
        assert g.nodes["w1"].depends_on == []


class TestDAGGraphValidate:
    def test_valid_dag(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        assert g.validate() == []

    def test_missing_dependency(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        errors = g.validate()
        assert any("missing" in e for e in errors)

    def test_self_cycle(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w1"]))
        errors = g.validate()
        assert any("depends on itself" in e for e in errors)

    def test_simple_cycle(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        errors = g.validate()
        assert any("Cycle" in e for e in errors)

    def test_complex_cycle(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w3"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w4"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w1"]))
        errors = g.validate()
        assert any("Cycle" in e for e in errors)

    def test_disconnected_nodes(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2"))
        g.add_node(DAGNode(worker_id="w3"))
        assert g.validate() == []

    def test_diamond_dag(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2", "w3"]))
        assert g.validate() == []

    def test_cycle_edge_via_removal(self):
        g = DAGGraph()
        g.add_dependency("w2", "w1")
        assert g.validate() == []
        g.add_dependency("w1", "w2")
        errors = g.validate()
        assert any("Cycle" in e for e in errors)

    def test_nested_disjoint_groups(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3"))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w3"]))
        assert g.validate() == []

    def test_complex_diamond_with_extra_edge(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2", "w3"]))
        errors = g.validate()
        assert errors == []


class TestDAGGraphTopologicalSort:
    def test_simple_linear(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        order = g.topological_sort()
        assert order.index("w1") < order.index("w2")
        assert order.index("w2") < order.index("w3")

    def test_diamond(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2", "w3"]))
        order = g.topological_sort()
        assert order.index("w1") < order.index("w2")
        assert order.index("w1") < order.index("w3")
        assert order.index("w2") < order.index("w4")
        assert order.index("w3") < order.index("w4")

    def test_multiple_roots(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2"))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1", "w2"]))
        order = g.topological_sort()
        assert order.index("w1") < order.index("w3")
        assert order.index("w2") < order.index("w3")

    def test_disjoint_groups(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3"))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w3"]))
        order = g.topological_sort()
        assert len(order) == 4
        assert order.index("w1") < order.index("w2")
        assert order.index("w3") < order.index("w4")

    def test_single_node(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        assert g.topological_sort() == ["w1"]

    def test_cycle_raises(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        with pytest.raises(ValueError, match="Cycle"):
            g.topological_sort()

    def test_missing_dep_raises(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        with pytest.raises(ValueError, match="missing"):
            g.topological_sort()

    def test_no_dep_chain(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2"))
        g.add_node(DAGNode(worker_id="w3"))
        order = g.topological_sort()
        assert set(order) == {"w1", "w2", "w3"}

    def test_complex_order_preserved(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w5", depends_on=["w2", "w3"]))
        g.add_node(DAGNode(worker_id="w6", depends_on=["w4", "w5"]))
        order = g.topological_sort()
        assert order[0] == "w1"
        assert order[-1] == "w6"


class TestDAGGraphReadyNodes:
    def test_no_deps(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2"))
        ready = g.ready_nodes(set())
        assert len(ready) == 2

    def test_all_deps_met(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        ready = g.ready_nodes({"w1"})
        assert len(ready) == 1
        assert ready[0].worker_id == "w2"

    def test_all_deps_met_one_level(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        ready = g.ready_nodes(set())
        assert len(ready) == 1
        assert ready[0].worker_id == "w1"
        ready = g.ready_nodes({"w1"})
        assert len(ready) == 1
        assert ready[0].worker_id == "w2"
        ready = g.ready_nodes({"w1", "w2"})
        assert len(ready) == 1
        assert ready[0].worker_id == "w3"

    def test_partial_deps(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        ready = g.ready_nodes(set())
        assert len(ready) == 1
        assert ready[0].worker_id == "w1"

    def test_none_ready(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        ready = g.ready_nodes(set())
        assert ready == []

    def test_multiple_upstream(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2"))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1", "w2"]))
        ready = g.ready_nodes({"w1"})
        assert len(ready) == 1
        assert ready[0].worker_id == "w2"
        ready = g.ready_nodes({"w1", "w2"})
        assert len(ready) == 1
        assert ready[0].worker_id == "w3"
        ready = g.ready_nodes(set())
        assert len(ready) == 2
        assert {r.worker_id for r in ready} == {"w1", "w2"}

    def test_skips_non_pending(self):
        g = DAGGraph()
        w1 = DAGNode(worker_id="w1")
        w1.status = DAGNodeStatus.COMPLETED
        g.add_node(w1)
        ready = g.ready_nodes(set())
        assert ready == []


class TestDAGGraphUpstreamDownstream:
    def test_get_upstream(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        upstream = g.get_upstream("w2")
        assert len(upstream) == 1
        assert upstream[0].worker_id == "w1"

    def test_get_upstream_none(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        assert g.get_upstream("w1") == []

    def test_get_upstream_not_found(self):
        g = DAGGraph()
        assert g.get_upstream("nonexistent") == []

    def test_get_downstream(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        downstream = g.get_downstream("w1")
        assert len(downstream) == 2
        assert {d.worker_id for d in downstream} == {"w2", "w3"}

    def test_get_downstream_none(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        assert g.get_downstream("nonexistent") == []


class TestDAGGraphReset:
    def test_reset_status(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.nodes["w1"].status = DAGNodeStatus.FAILED
        g.nodes["w1"].error = "err"
        g.nodes["w2"].status = DAGNodeStatus.SKIPPED
        g.reset_status()
        assert g.nodes["w1"].status == DAGNodeStatus.PENDING
        assert g.nodes["w1"].error == ""
        assert g.nodes["w2"].status == DAGNodeStatus.PENDING


class TestDAGGraphSerialization:
    def test_to_dict(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        d = g.to_dict()
        assert "nodes" in d
        assert "w1" in d["nodes"]
        assert "w2" in d["nodes"]
        assert d["nodes"]["w2"]["depends_on"] == ["w1"]

    def test_from_dict(self):
        data = {
            "nodes": {
                "w1": {
                    "worker_id": "w1",
                    "depends_on": [],
                    "metadata": {},
                    "status": "pending",
                    "error": "",
                },
                "w2": {
                    "worker_id": "w2",
                    "depends_on": ["w1"],
                    "metadata": {},
                    "status": "pending",
                    "error": "",
                },
            }
        }
        g = DAGGraph.from_dict(data)
        assert "w1" in g.nodes
        assert "w2" in g.nodes
        assert g.nodes["w2"].depends_on == ["w1"]

    def test_from_dict_empty(self):
        g = DAGGraph.from_dict({"nodes": {}})
        assert g.nodes == {}

    def test_to_dict_round_trip(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"], metadata={"env": "test"}))
        restored = DAGGraph.from_dict(g.to_dict())
        assert len(restored.nodes) == 3
        assert restored.nodes["w3"].depends_on == ["w2"]
        assert restored.nodes["w3"].metadata == {"env": "test"}

    def test_find_cycle_no_cycle(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        assert g._find_cycle() == []

    def test_find_cycle_simple(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        cycle = g._find_cycle()
        assert len(cycle) >= 2

    def test_find_cycle_disjoint_groups_no_cycle(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2"))
        g.add_node(DAGNode(worker_id="w3"))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w3"]))
        assert g._find_cycle() == []

    def test_find_cycle_complex(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1", depends_on=["w2"]))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w3"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w4"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w5", depends_on=["w1"]))
        cycle = g._find_cycle()
        assert len(cycle) >= 2


class TestDAGOrchestrator:
    def test_init_defaults(self):
        orch = DAGOrchestrator()
        assert orch.graph.nodes == {}
        assert orch._a2a is None
        assert orch._trust_scorer is None
        assert orch._execution_timeout == 300.0
        assert orch.execution_history == []
        assert orch.running is False

    def test_graph_property(self):
        orch = DAGOrchestrator()
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        orch.graph = g
        assert "w1" in orch.graph.nodes

    def test_get_execution_plan(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        orch = DAGOrchestrator(graph=g)
        plan = orch.get_execution_plan()
        assert plan == ["w1", "w2", "w3"]

    def test_get_execution_plan_by_level_linear(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        orch = DAGOrchestrator(graph=g)
        levels = orch.get_execution_plan_by_level()
        assert levels == [["w1"], ["w2"], ["w3"]]

    def test_get_execution_plan_by_level_diamond(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2", "w3"]))
        orch = DAGOrchestrator(graph=g)
        levels = orch.get_execution_plan_by_level()
        assert len(levels) == 3
        assert levels[0] == ["w1"]
        assert set(levels[1]) == {"w2", "w3"}
        assert levels[2] == ["w4"]

    def test_estimate_trust_reliability_no_scorer(self):
        orch = DAGOrchestrator()
        assert orch.estimate_trust_reliability("anything") == 1.0

    def test_estimate_trust_reliability_no_report(self):
        scorer = MagicMock()
        scorer.get_latest.return_value = None
        orch = DAGOrchestrator(trust_scorer=scorer)
        assert orch.estimate_trust_reliability("w1") == 1.0

    def test_estimate_trust_reliability_uses_score(self):
        scorer = MagicMock()
        report = MagicMock()
        report.overall_score = 0.85
        scorer.get_latest.return_value = report
        orch = DAGOrchestrator(trust_scorer=scorer)
        assert orch.estimate_trust_reliability("w1") == 0.85

    def test_execute_node_not_in_graph(self):
        orch = DAGOrchestrator()
        result = asyncio.run(orch.execute_node("nonexistent"))
        assert result is False

    def test_execute_node_no_a2a(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        orch = DAGOrchestrator(graph=g)
        result = asyncio.run(orch.execute_node("w1"))
        assert result is True
        assert g.nodes["w1"].status == DAGNodeStatus.COMPLETED

    def test_execute_node_low_trust(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        scorer = MagicMock()
        report = MagicMock()
        report.overall_score = 0.2
        scorer.get_latest.return_value = report
        orch = DAGOrchestrator(graph=g, trust_scorer=scorer)
        result = asyncio.run(orch.execute_node("w1"))
        assert result is False
        assert g.nodes["w1"].status == DAGNodeStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_execute_node_a2a_success(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute_node("w1")
        assert result is True
        assert g.nodes["w1"].status == DAGNodeStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_node_a2a_failure(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = False
        resp.error = "handler failed"
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute_node("w1")
        assert result is False
        assert g.nodes["w1"].status == DAGNodeStatus.FAILED
        assert g.nodes["w1"].error == "handler failed"

    @pytest.mark.asyncio
    async def test_execute_node_a2a_exception(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        a2a.send_request = AsyncMock(side_effect=RuntimeError("timeout"))
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute_node("w1")
        assert result is False
        assert g.nodes["w1"].status == DAGNodeStatus.FAILED

    def test_to_dict(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        orch = DAGOrchestrator(graph=g)
        d = orch.to_dict()
        assert "graph" in d
        assert "execution_history" in d
        assert d["running"] is False
        assert "w1" in d["graph"]["nodes"]

    def test_running_property(self):
        orch = DAGOrchestrator()
        assert orch.running is False

    def test_execution_history_property(self):
        orch = DAGOrchestrator()
        assert orch.execution_history == []

    def test_execute_no_a2a_simple(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        orch = DAGOrchestrator(graph=g)
        result = asyncio.run(orch.execute())
        assert result["success"] is True
        assert result["completed"] == ["w1", "w2"]
        assert result["failed"] == []
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_execute_diamond(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w4", depends_on=["w2", "w3"]))
        orch = DAGOrchestrator(graph=g)
        result = await orch.execute()
        assert result["success"] is True
        assert set(result["completed"]) == {"w1", "w2", "w3", "w4"}

    @pytest.mark.asyncio
    async def test_execute_idempotent(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        orch = DAGOrchestrator(graph=g)
        r1 = await orch.execute()
        assert r1["success"] is True
        r2 = await orch.execute()
        assert r2["success"] is True

    @pytest.mark.asyncio
    async def test_execute_raises_if_running(self):
        orch = DAGOrchestrator()
        orch._running = True
        with pytest.raises(RuntimeError, match="already running"):
            await orch.execute()

    @pytest.mark.asyncio
    async def test_execute_a2a_success(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute()
        assert result["success"] is True
        assert result["completed"] == ["w1"]

    @pytest.mark.asyncio
    async def test_execute_a2a_stops_on_failure(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        a2a = AsyncMock()
        fail_resp = MagicMock()
        fail_resp.success = False
        fail_resp.error = "fail"
        a2a.send_request = AsyncMock(return_value=fail_resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute(stop_on_failure=True)
        assert result["success"] is False
        assert "w1" in result["failed"]
        assert result["skipped"] == ["w2"]

    @pytest.mark.asyncio
    async def test_execute_a2a_continues_on_failure(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        a2a = AsyncMock()
        fail_resp = MagicMock()
        fail_resp.success = False
        fail_resp.error = "fail"
        a2a.send_request = AsyncMock(return_value=fail_resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute(stop_on_failure=False)
        assert result["success"] is False
        assert "w1" in result["failed"]

    @pytest.mark.asyncio
    async def test_execute_node_with_ttl(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a, execution_timeout=10.0)
        assert orch._execution_timeout == 10.0
        await orch.execute_node("w1")
        a2a.send_request.assert_awaited_once()
        call_kwargs = a2a.send_request.call_args.kwargs
        assert call_kwargs["timeout"] == 10.0

    @pytest.mark.asyncio
    async def test_execute_history_appended(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        orch = DAGOrchestrator(graph=g)
        await orch.execute_node("w1")
        assert len(orch.execution_history) == 1
        assert orch.execution_history[0]["worker_id"] == "w1"

    def test_execution_plan_empty_graph(self):
        orch = DAGOrchestrator()
        assert orch.get_execution_plan() == []

    def test_execution_plan_by_level_empty(self):
        orch = DAGOrchestrator()
        assert orch.get_execution_plan_by_level() == []

    def test_execute_node_with_custom_payload(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = asyncio.run(
            orch.execute_node("w1", action="custom_action", payload={"x": 1})
        )
        assert result is True
        a2a.send_request.assert_called_once_with(
            target_worker="w1",
            action="custom_action",
            payload={"x": 1},
            timeout=pytest.approx(300.0, rel=0.1),
        )

    @pytest.mark.asyncio
    async def test_execute_with_custom_action_and_payload(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute(action="deploy", payload={"version": "v2"})
        assert result["success"] is True
        a2a.send_request.assert_called_once_with(
            target_worker="w1",
            action="deploy",
            payload={"version": "v2"},
            timeout=pytest.approx(300.0, rel=0.1),
        )

    @pytest.mark.asyncio
    async def test_execute_graph_with_multiple_levels(self):
        g = DAGGraph()
        g.add_node(DAGNode(worker_id="w1"))
        g.add_node(DAGNode(worker_id="w2", depends_on=["w1"]))
        g.add_node(DAGNode(worker_id="w3", depends_on=["w2"]))
        a2a = AsyncMock()
        resp = MagicMock()
        resp.success = True
        a2a.send_request = AsyncMock(return_value=resp)
        orch = DAGOrchestrator(graph=g, a2a_protocol=a2a)
        result = await orch.execute()
        assert result["success"] is True
        assert a2a.send_request.await_count == 3
