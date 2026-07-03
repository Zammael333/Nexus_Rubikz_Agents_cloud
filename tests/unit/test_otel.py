from __future__ import annotations

import pytest

from app.otel.injector import (
    _OTEL_AVAILABLE,
    OtelInjector,
    _is_async,
    instrument_worker,
    otel_traced,
)

skip_when_otel = pytest.mark.skipif(
    _OTEL_AVAILABLE, reason="OTEL is installed in this environment"
)

pytestmark = pytest.mark.asyncio(scope="function")


@skip_when_otel
def test_otel_availability():
    assert _OTEL_AVAILABLE is False


def test_otel_traced_noop_without_otel():
    call_count = 0

    @otel_traced(span_name="test_span", attributes={"key": "val"})
    def sync_fn():
        nonlocal call_count
        call_count += 1
        return 42

    result = sync_fn()
    assert result == 42
    assert call_count == 1


def test_otel_traced_noop_preserves_metadata():
    @otel_traced()
    def sync_fn():
        return "ok"

    assert sync_fn() == "ok"


def test_otel_traced_noop_with_exception():
    @otel_traced()
    def sync_fn():
        msg = "fail"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="fail"):
        sync_fn()


def test_otel_traced_noop_no_span_name():
    @otel_traced()
    def my_function():
        return 99

    assert my_function() == 99


def test_otel_traced_noop_empty_attrs():
    @otel_traced(span_name="empty", attributes={})
    def fn():
        return True

    assert fn() is True


class TestOtelInjector:
    def test_init_defaults(self):
        injector = OtelInjector()
        assert injector._service_name == "nexus-rubykz"
        if _OTEL_AVAILABLE:
            assert injector._tracer is not None
            assert injector._meter is not None
        else:
            assert injector._tracer is None
            assert injector._meter is None

    def test_init_custom_service(self):
        injector = OtelInjector(service_name="custom")
        assert injector._service_name == "custom"

    @skip_when_otel
    def test_tracer_none_without_otel(self):
        assert OtelInjector().tracer() is None

    @skip_when_otel
    def test_meter_none_without_otel(self):
        assert OtelInjector().meter() is None

    def test_counter_noop_without_otel(self):
        injector = OtelInjector()
        c = injector.counter("test.counter", "Test counter")
        c.add(5)
        assert c._name == "test.counter"

    def test_counter_reuses_instance(self):
        injector = OtelInjector()
        c1 = injector.counter("dup")
        c2 = injector.counter("dup")
        assert c1 is c2

    def test_histogram_noop_without_otel(self):
        injector = OtelInjector()
        h = injector.histogram("test.histogram", "Test histogram")
        h.record(1.5)
        assert h._name == "test.histogram"

    def test_instrument_dag_orchestrator_noop_without_otel(self):
        injector = OtelInjector()
        mock_dag = _MockDAG()
        injector.instrument_dag_orchestrator(mock_dag)
        assert mock_dag.instrumented is False

    @skip_when_otel
    def test_instrumented_flag_not_set_without_otel(self):
        from app.otel.injector import _INSTRUMENTED_WORKERS

        _INSTRUMENTED_WORKERS.clear()
        assert "w1" not in _INSTRUMENTED_WORKERS
        instrument_worker("w1")
        assert "w1" not in _INSTRUMENTED_WORKERS

    def test_instrument_worker_twice_noop(self):
        from app.otel.injector import _INSTRUMENTED_WORKERS

        _INSTRUMENTED_WORKERS.clear()
        d1 = instrument_worker("w1")
        d2 = instrument_worker("w1")
        assert d1 is not d2

    def test_otel_traced_preserves_wrapped_name(self):
        @otel_traced(span_name="renamed")
        def my_func():
            return 1

        assert my_func() == 1


def test_is_async_sync_function():
    def sync():
        pass

    assert _is_async(sync) is False


def test_is_async_async_function():

    async def async_fn():
        pass

    assert _is_async(async_fn) is True


class TestOtelInjectorInstrumentDAG:
    def test_instrument_replaces_execute_node(self):
        injector = OtelInjector()
        dag = _MockDAG()
        original = dag.execute_node
        injector.instrument_dag_orchestrator(dag)
        assert dag.execute_node is not original

    async def test_traced_execute_node_returns_original_result(self):
        injector = OtelInjector()
        dag = _MockDAG()
        injector.instrument_dag_orchestrator(dag)
        result = await dag.execute_node("w1")
        assert result is True

    @skip_when_otel
    def test_otel_availabe_false(self):
        assert _OTEL_AVAILABLE is False


class _MockDAG:
    def __init__(self):
        self._graph = _MockGraph()
        self._execution_timeout = 30.0
        self._a2a = None
        self._execution_history = []
        self._running = False
        self.instrumented = False

    async def execute_node(self, worker_id, action="execute", payload=None):
        self.instrumented = True
        return True


class _MockGraph:
    def __init__(self):
        self.nodes = {"w1": _MockNode(), "w2": _MockNode()}


class _MockNode:
    def __init__(self):
        self.status = "pending"
