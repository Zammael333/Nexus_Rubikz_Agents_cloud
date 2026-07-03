import asyncio
import json
import logging
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

try:
    from opentelemetry import trace as otel_trace

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DeliveryGuarantee(Enum):
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"


@dataclass
class BusEvent:
    type: str
    payload: dict[str, Any]
    source: str
    priority: EventPriority = EventPriority.NORMAL
    event_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    retry_count: int = 0
    recovery_epoch: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "priority": self.priority.name,
            "event_uuid": self.event_uuid,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "recovery_epoch": self.recovery_epoch,
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class DeadLetterRecord:
    def __init__(self, event: BusEvent, reason: str, failed_at: str = ""):
        self.event = event
        self.reason = reason
        self.failed_at = failed_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "reason": self.reason,
            "failed_at": self.failed_at,
        }


class AsyncEventBus:
    def __init__(
        self,
        max_queue_size: int = 10000,
        batch_size: int = 10,
        flush_interval: float = 2.0,
        log_file: str = "nexus_telemetry.log",
        delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
        max_retries: int = 3,
        remote_delivery_hook: Callable[[list[BusEvent]], None] | None = None,
        tracer: Any = None,
    ):
        self.queue: asyncio.Queue[BusEvent] = asyncio.Queue(maxsize=max_queue_size)
        self.priority_queue: asyncio.Queue[BusEvent] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_file = log_file
        self.delivery_guarantee = delivery_guarantee
        self.max_retries = max_retries
        self.remote_delivery_hook = remote_delivery_hook
        self._tracer: Any = tracer or (
            otel_trace.get_tracer("nexus.bus") if _OTEL_AVAILABLE else None
        )
        self._running = False
        self._consumer_task: asyncio.Task | None = None
        self._batch: list[BusEvent] = []
        self._dlq: list[DeadLetterRecord] = []
        self._event_count = 0
        self._recovery_epoch = str(uuid.uuid4())
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._recovery_epoch = str(uuid.uuid4())
        self._consumer_task = asyncio.create_task(self._consumer_loop())
        logger.info(
            f"[ASYNC_BUS] Started. Recovery epoch: {self._recovery_epoch[:8]}..."
        )

    async def stop(self) -> list[DeadLetterRecord]:
        self._running = False
        if self._consumer_task:
            try:
                await asyncio.wait_for(self._consumer_task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                logger.warning("[ASYNC_BUS] Consumer did not stop cleanly.")
        if self._batch:
            await self._flush_batch()
        dlq_len = len(self._dlq)
        logger.info(f"[ASYNC_BUS] Stopped. {dlq_len} events in Dead-Letter Queue.")
        if self._tracer:
            current_span = otel_trace.get_current_span()
            current_span.set_attribute("bus.dlq_count", dlq_len)
            current_span.set_attribute("bus.event_count", self._event_count)
        return self._dlq

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
    ) -> bool:
        event = BusEvent(
            type=event_type,
            payload=payload,
            source=source,
            priority=priority,
            recovery_epoch=self._recovery_epoch,
        )
        attrs = {
            "event.type": event_type,
            "event.source": source,
            "event.priority": priority.name,
            "event.uuid": event.event_uuid,
            "bus.recovery_epoch": self._recovery_epoch,
        }
        if self._tracer:
            with self._tracer.start_as_current_span(
                "bus.emit", attributes=attrs
            ) as span:
                return await self._emit_inner(event, priority, span)
        return await self._emit_inner(event, priority)

    async def _emit_inner(
        self,
        event: BusEvent,
        priority: EventPriority,
        span: Any = None,
    ) -> bool:
        target = (
            self.priority_queue if priority == EventPriority.CRITICAL else self.queue
        )
        try:
            await asyncio.wait_for(target.put(event), timeout=1.0)
            self._event_count += 1
            if span:
                span.set_attribute("bus.outcome", "enqueued")
            return True
        except TimeoutError:
            self._send_to_dlq(event, reason="BACKPRESSURE_TIMEOUT")
            if span:
                span.set_attribute("bus.outcome", "backpressure_dlq")
            logger.warning(f"[ASYNC_BUS] Backpressure: event {event.type} sent to DLQ")
            return False

    async def _consumer_loop(self) -> None:
        while self._running:
            try:
                if self._tracer:
                    with self._tracer.start_as_current_span("bus.consume.poll"):
                        event = await asyncio.wait_for(
                            self._drain_any(), timeout=self.flush_interval
                        )
                else:
                    event = await asyncio.wait_for(
                        self._drain_any(), timeout=self.flush_interval
                    )
                self._batch.append(event)
                if len(self._batch) >= self.batch_size:
                    await self._flush_batch()
            except TimeoutError:
                if self._batch:
                    await self._flush_batch()

    async def _drain_any(self) -> BusEvent:
        while True:
            if not self.priority_queue.empty():
                return await self.priority_queue.get()
            return await self.queue.get()

    async def _flush_batch(self) -> None:
        async with self._lock:
            batch = self._batch
            self._batch = []
        if not batch:
            return
        attrs = {
            "bus.batch_size": len(batch),
            "bus.log_file": self.log_file,
        }
        if self._tracer:
            with self._tracer.start_as_current_span(
                "bus.flush", attributes=attrs
            ) as span:
                self._write_local(batch)
                if self.remote_delivery_hook:
                    await self._deliver_remote(batch, span)
        else:
            self._write_local(batch)
            if self.remote_delivery_hook:
                await self._deliver_remote(batch)

    def _write_local(self, batch: list[BusEvent]) -> None:
        try:
            os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
            with open(self.log_file, "a") as f:
                for event in batch:
                    f.write(f"[EVENT_BUS] [{event.type}] {event}\n")
        except OSError as e:
            logger.error(f"[ASYNC_BUS] Local write failed: {e}")
            for event in batch:
                self._send_to_dlq(event, reason=f"LOCAL_WRITE_FAILED: {e}")

    async def _deliver_remote(self, batch: list[BusEvent], span: Any = None) -> None:
        if not self.remote_delivery_hook:
            return
        try:
            if self.delivery_guarantee == DeliveryGuarantee.AT_LEAST_ONCE:
                for event in batch:
                    try:
                        self.remote_delivery_hook([event])
                    except Exception as e:
                        event.retry_count += 1
                        if event.retry_count > self.max_retries:
                            self._send_to_dlq(
                                event, reason=f"MAX_RETRIES_EXCEEDED: {e}"
                            )
                        else:
                            await self.queue.put(event)
            else:
                self.remote_delivery_hook(batch)
            if span:
                span.set_attribute("bus.delivery_outcome", "delivered")
        except Exception as e:
            if span:
                span.set_attribute("bus.delivery_outcome", "failed")
                span.record_exception(e)
            logger.error(f"[ASYNC_BUS] Remote delivery failed: {e}")

    def _send_to_dlq(self, event: BusEvent, reason: str = "UNKNOWN") -> None:
        self._dlq.append(DeadLetterRecord(event=event, reason=reason))
        if self._tracer:
            current_span = otel_trace.get_current_span()
            current_span.add_event(
                "bus.dlq",
                attributes={
                    "event.uuid": event.event_uuid,
                    "event.type": event.type,
                    "bus.dlq_reason": reason,
                },
            )

    @property
    def dlq_size(self) -> int:
        return len(self._dlq)

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def queue_size(self) -> int:
        return self.queue.qsize() + self.priority_queue.qsize()

    def recover_dlq(self) -> list[DeadLetterRecord]:
        recovered = []
        remaining = []
        for record in self._dlq:
            record.event.retry_count = 0
            try:
                self.queue.put_nowait(record.event)
                recovered.append(record)
            except asyncio.QueueFull:
                remaining.append(record)
        self._dlq = remaining
        return recovered
