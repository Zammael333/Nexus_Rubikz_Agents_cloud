from __future__ import annotations

import functools
import logging
import time
from typing import Any

try:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry import trace as otel_trace

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)


def otel_traced(
    span_name: str | None = None,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Any:
    if not _OTEL_AVAILABLE:

        def noop_decorator(fn: Any) -> Any:
            return fn

        return noop_decorator

    tracer = otel_trace.get_tracer(__name__)

    def decorator(fn: Any) -> Any:
        is_async = _is_async(fn)

        @functools.wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            name = span_name or fn.__name__
            with tracer.start_as_current_span(name) as span:
                for k, v in (attributes or {}).items():
                    span.set_attribute(k, str(v))
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    if record_exception:
                        span.record_exception(e)
                        span.set_status(
                            otel_trace.Status(otel_trace.StatusCode.ERROR, str(e))
                        )
                    raise

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            name = span_name or fn.__name__
            with tracer.start_as_current_span(name) as span:
                for k, v in (attributes or {}).items():
                    span.set_attribute(k, str(v))
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if record_exception:
                        span.record_exception(e)
                        span.set_status(
                            otel_trace.Status(otel_trace.StatusCode.ERROR, str(e))
                        )
                    raise

        return async_wrapper if is_async else sync_wrapper

    return decorator


def _is_async(fn: Any) -> bool:
    import asyncio
    import inspect

    return asyncio.iscoroutinefunction(fn) or inspect.iscoroutinefunction(fn)


class OtelInjector:
    def __init__(self, service_name: str = "nexus-rubykz") -> None:
        self._service_name = service_name
        self._tracer = otel_trace.get_tracer(service_name) if _OTEL_AVAILABLE else None
        self._meter = otel_metrics.get_meter(service_name) if _OTEL_AVAILABLE else None
        self._counters: dict[str, Any] = {}

    def tracer(self) -> Any:
        return self._tracer

    def meter(self) -> Any:
        return self._meter

    def counter(self, name: str, description: str = "") -> Any:
        if name not in self._counters:
            if self._meter:
                self._counters[name] = self._meter.create_counter(
                    name, description=description
                )
            else:
                self._counters[name] = _NoopCounter(name)
        return self._counters[name]

    def histogram(self, name: str, description: str = "") -> Any:
        if self._meter:
            return self._meter.create_histogram(name, description=description)
        return _NoopHistogram(name)

    def instrument_dag_orchestrator(
        self,
        dag_orchestrator: Any,
    ) -> None:
        if not _OTEL_AVAILABLE:
            return
        node_counter = self.counter("dag.nodes.total", "Total nodes executed")
        node_duration = self.histogram(
            "dag.node.duration", "Node execution duration (s)"
        )
        original_execute = dag_orchestrator.execute_node

        async def traced_execute_node(
            worker_id: str,
            action: str = "execute",
            payload: dict[str, Any] | None = None,
        ) -> bool:
            start = time.monotonic()
            with self._tracer.start_as_current_span(
                f"dag.node.{worker_id}",
                attributes={
                    "worker.id": worker_id,
                    "dag.action": action,
                    "service.name": self._service_name,
                },
            ) as span:
                try:
                    result = await original_execute(worker_id, action, payload)
                    elapsed = time.monotonic() - start
                    span.set_attribute("dag.node.duration_s", elapsed)
                    node_duration.record(elapsed, {"worker.id": worker_id})
                    node_counter.add(1, {"worker.id": worker_id, "status": "ok"})
                    if not result:
                        span.set_attribute("dag.node.status", "failed")
                    return result
                except Exception as e:
                    elapsed = time.monotonic() - start
                    span.record_exception(e)
                    span.set_status(
                        otel_trace.Status(otel_trace.StatusCode.ERROR, str(e))
                    )
                    node_duration.record(elapsed, {"worker.id": worker_id})
                    node_counter.add(1, {"worker.id": worker_id, "status": "error"})
                    raise

        dag_orchestrator.execute_node = traced_execute_node
        n_workers = len(dag_orchestrator._graph.nodes)
        logger.info(f"[OTEL] DAGOrchestrator instrumented ({n_workers} workers)")


_INSTRUMENTED_WORKERS: set[str] = set()


def instrument_worker(worker_id: str) -> Any:
    if not _OTEL_AVAILABLE:
        return lambda fn: fn

    if worker_id in _INSTRUMENTED_WORKERS:
        return lambda fn: fn

    _INSTRUMENTED_WORKERS.add(worker_id)

    def decorator(fn: Any) -> Any:
        return otel_traced(
            span_name=f"worker.{worker_id}",
            attributes={
                "worker.id": worker_id,
                "service.name": "nexus-rubykz",
            },
        )(fn)

    return decorator


class _NoopCounter:
    def __init__(self, name: str) -> None:
        self._name = name

    def add(self, amount: int = 1, attributes: dict[str, str] | None = None) -> None:
        pass


class _NoopHistogram:
    def __init__(self, name: str) -> None:
        self._name = name

    def record(self, amount: float, attributes: dict[str, str] | None = None) -> None:
        pass
