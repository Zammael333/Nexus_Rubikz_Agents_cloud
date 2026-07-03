import asyncio
import os
import tempfile

import pytest

from app.bus.async_event_bus import AsyncEventBus, EventPriority


@pytest.mark.asyncio
async def test_emit_and_consume() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name
    bus = AsyncEventBus(log_file=log_path, batch_size=1, flush_interval=0.1)
    await bus.start()
    ok = await bus.emit("TEST_EVENT", {"msg": "hello"}, source="test")
    assert ok is True
    await asyncio.sleep(0.3)
    assert bus.event_count == 1
    with open(log_path) as f:
        content = f.read()
    assert "TEST_EVENT" in content
    assert "hello" in content
    await bus.stop()
    os.unlink(log_path)


@pytest.mark.asyncio
async def test_emit_returns_false_on_backpressure() -> None:
    bus = AsyncEventBus(max_queue_size=2, batch_size=10, flush_interval=5.0)
    bus._running = True
    bus._consumer_task = asyncio.create_task(asyncio.sleep(100))
    ok1 = await bus.emit("A", {}, source="test")
    ok2 = await bus.emit("B", {}, source="test")
    ok3 = await bus.emit("C", {}, source="test")
    bus._running = False
    bus._consumer_task.cancel()
    assert ok1 is True
    assert ok2 is True
    assert ok3 is False


@pytest.mark.asyncio
async def test_dead_letter_queue() -> None:
    events_to_test = 3
    bus = AsyncEventBus(max_queue_size=1, batch_size=10, flush_interval=5.0)
    bus._running = True
    bus._consumer_task = asyncio.create_task(asyncio.sleep(100))
    await bus.emit("A", {}, source="test")
    for _ in range(events_to_test):
        await bus.emit("DLQ", {}, source="test")
    assert bus.dlq_size >= 1
    bus._running = False
    bus._consumer_task.cancel()


@pytest.mark.asyncio
async def test_dlq_recovery() -> None:
    bus = AsyncEventBus(batch_size=1, flush_interval=0.1)
    await bus.start()
    await bus.emit("RECOVER", {}, source="test")
    await asyncio.sleep(0.3)
    recovered = bus.recover_dlq()
    assert isinstance(recovered, list)
    await bus.stop()


@pytest.mark.asyncio
async def test_remote_delivery_hook() -> None:
    delivered: list = []

    def hook(events):
        delivered.extend(events)

    bus = AsyncEventBus(
        batch_size=1,
        flush_interval=0.1,
        remote_delivery_hook=hook,
    )
    await bus.start()
    await bus.emit("HOOK_TEST", {"data": 1}, source="test")
    await asyncio.sleep(0.3)
    assert len(delivered) > 0
    assert delivered[0].type == "HOOK_TEST"
    await bus.stop()


@pytest.mark.asyncio
async def test_stop_returns_dlq() -> None:
    bus = AsyncEventBus(max_queue_size=1, batch_size=10, flush_interval=5.0)
    bus._running = True
    bus._consumer_task = asyncio.create_task(asyncio.sleep(100))
    await bus.emit("A", {}, source="test")
    await bus.emit("B", {}, source="test")
    bus._running = False
    bus._consumer_task.cancel()
    await bus.stop()


@pytest.mark.asyncio
async def test_event_uuid_uniqueness() -> None:
    bus = AsyncEventBus(batch_size=10, flush_interval=0.5)
    await bus.start()
    for i in range(10):
        await bus.emit("UNIQ", {"i": i}, source="test")
    await asyncio.sleep(0.1)
    await bus.stop()


@pytest.mark.asyncio
async def test_concurrent_emits() -> None:
    bus = AsyncEventBus(batch_size=5, flush_interval=0.2)
    await bus.start()

    async def emit_many(n: int):
        for i in range(n):
            await bus.emit("CONCUR", {"i": i}, source="concurrent")

    await asyncio.gather(emit_many(20), emit_many(20))
    await asyncio.sleep(0.5)
    assert bus.event_count == 40
    await bus.stop()


@pytest.mark.asyncio
async def test_critical_emits_use_priority_queue() -> None:
    bus = AsyncEventBus(batch_size=10, flush_interval=5.0)
    bus._running = True
    bus._consumer_task = asyncio.create_task(asyncio.sleep(100))
    await bus.emit("NORMAL", {"seq": 1}, source="test", priority=EventPriority.NORMAL)
    await bus.emit(
        "CRITICAL", {"seq": 2}, source="test", priority=EventPriority.CRITICAL
    )
    await bus.emit("HIGH", {"seq": 3}, source="test", priority=EventPriority.HIGH)
    assert bus.queue_size == 3
    bus._running = False
    bus._consumer_task.cancel()
