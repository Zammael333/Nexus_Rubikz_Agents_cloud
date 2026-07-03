import asyncio
import os
import tempfile

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from app.bus.async_event_bus import AsyncEventBus, EventPriority


@pytest.fixture
def span_exporter():
    return InMemorySpanExporter()


@pytest.fixture
def tracer(span_exporter):
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    return provider.get_tracer("test.bus")


@pytest.mark.asyncio
async def test_emit_creates_span(span_exporter, tracer) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name
    bus = AsyncEventBus(
        log_file=log_path, batch_size=1, flush_interval=0.1, tracer=tracer
    )
    await bus.start()
    ok = await bus.emit("OTEL_TEST", {"msg": "otel"}, source="test_otel")
    assert ok is True
    await asyncio.sleep(0.5)
    await bus.stop()
    os.unlink(log_path)

    spans = span_exporter.get_finished_spans()
    span_names = [s.name for s in spans]
    assert "bus.emit" in span_names
    assert "bus.flush" in span_names

    emit_span = next(s for s in spans if s.name == "bus.emit")
    assert emit_span.attributes.get("event.type") == "OTEL_TEST"
    assert emit_span.attributes.get("event.source") == "test_otel"
    assert emit_span.attributes.get("event.priority") == "NORMAL"
    assert emit_span.attributes.get("bus.outcome") == "enqueued"


@pytest.mark.asyncio
async def test_critical_emit_priority_span(span_exporter, tracer) -> None:
    bus = AsyncEventBus(batch_size=10, flush_interval=0.2, tracer=tracer)
    await bus.start()
    await bus.emit("CRIT", {}, source="test", priority=EventPriority.CRITICAL)
    await asyncio.sleep(0.3)
    await bus.stop()

    spans = span_exporter.get_finished_spans()
    emit_span = next(s for s in spans if s.name == "bus.emit")
    assert emit_span.attributes.get("event.priority") == "CRITICAL"


@pytest.mark.asyncio
async def test_backpressure_dlq_records_otel_event(span_exporter, tracer) -> None:
    bus = AsyncEventBus(
        max_queue_size=1, batch_size=10, flush_interval=5.0, tracer=tracer
    )
    bus._running = True
    bus._consumer_task = asyncio.create_task(asyncio.sleep(100))
    await bus.emit("A", {}, source="test")
    await bus.emit("B", {}, source="test")
    bus._running = False
    bus._consumer_task.cancel()
    await bus.stop()

    spans = span_exporter.get_finished_spans()
    emit_spans = [s for s in spans if s.name == "bus.emit"]
    assert len(emit_spans) >= 1
    backpressure_span = next(
        (
            s
            for s in emit_spans
            if s.attributes.get("bus.outcome") == "backpressure_dlq"
        ),
        None,
    )
    assert backpressure_span is not None


@pytest.mark.asyncio
async def test_flush_span_has_batch_size(span_exporter, tracer) -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name
    bus = AsyncEventBus(
        log_file=log_path, batch_size=2, flush_interval=0.1, tracer=tracer
    )
    await bus.start()
    await bus.emit("BATCH1", {}, source="test")
    await bus.emit("BATCH2", {}, source="test")
    await asyncio.sleep(0.5)
    await bus.stop()
    os.unlink(log_path)

    spans = span_exporter.get_finished_spans()
    flush_spans = [s for s in spans if s.name == "bus.flush"]
    assert len(flush_spans) >= 1
    assert flush_spans[0].attributes.get("bus.batch_size") == 2


@pytest.mark.asyncio
async def test_no_tracer_does_not_crash(span_exporter) -> None:
    bus = AsyncEventBus(batch_size=1, flush_interval=0.1, tracer=None)
    await bus.start()
    ok = await bus.emit("NO_TRACER", {}, source="test")
    assert ok is True
    await asyncio.sleep(0.3)
    dlq = await bus.stop()
    assert isinstance(dlq, list)


@pytest.mark.asyncio
async def test_default_tracer_fallback() -> None:
    bus = AsyncEventBus(batch_size=1, flush_interval=0.1)
    assert bus._tracer is not None
    await bus.start()
    ok = await bus.emit("DEFAULT", {}, source="test")
    assert ok is True
    await asyncio.sleep(0.3)
    await bus.stop()
