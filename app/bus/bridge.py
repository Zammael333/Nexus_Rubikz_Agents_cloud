# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — SyncBusBridge (Option B: Bridge Pattern)
#
# Provides a synchronous facade over AsyncEventBus so that ADK tool functions
# (which are synchronous) can emit events without calling asyncio directly.
# The bridge manages its own event loop in a background daemon thread.

import asyncio
import atexit
import logging
import threading
from typing import Any

from app.bus.async_event_bus import AsyncEventBus, DeliveryGuarantee, EventPriority

logger = logging.getLogger(__name__)


class SyncBusBridge:
    """Synchronous facade over AsyncEventBus.

    ADK tool functions are synchronous.  This bridge runs an AsyncEventBus
    inside a dedicated background thread with its own event loop, and exposes
    a blocking ``emit()`` method that workers can call from sync code.

    Usage::

        bus = SyncBusBridge()
        bus.start()
        bus.emit("INVENTORY_LOCK_ATTEMPT", {"sku": "X1"}, source="worker")
        dlq = bus.stop()
    """

    def __init__(
        self,
        max_queue_size: int | None = None,
        batch_size: int | None = None,
        flush_interval: float | None = None,
        log_file: str | None = None,
        delivery_guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
        max_retries: int = 3,
        remote_delivery_hook: Any = None,
        tracer: Any = None,
    ):
        from app.config import settings
        self._async_bus = AsyncEventBus(
            max_queue_size=max_queue_size or settings.bus_max_queue_size,
            batch_size=batch_size or settings.bus_batch_size,
            flush_interval=flush_interval or settings.bus_flush_interval,
            log_file=log_file or settings.bus_log_file,
            delivery_guarantee=delivery_guarantee,
            max_retries=max_retries,
            remote_delivery_hook=remote_delivery_hook,
            tracer=tracer,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = False

    @property
    def async_bus(self) -> AsyncEventBus:
        """Direct access to the underlying async bus (for advanced usage)."""
        return self._async_bus

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Start the background event loop and the async bus consumer."""
        if self._started:
            return
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="nexus-bus-bridge"
        )
        self._thread.start()
        # Block until the async bus is running inside the background loop
        future = asyncio.run_coroutine_threadsafe(self._async_bus.start(), self._loop)
        future.result(timeout=5.0)
        self._started = True
        atexit.register(self.stop)
        logger.info("[SYNC_BRIDGE] Started.")

    def stop(self) -> list:
        """Stop the bus, drain remaining events, and return DLQ."""
        if not self._started or self._loop is None:
            return []
        future = asyncio.run_coroutine_threadsafe(self._async_bus.stop(), self._loop)
        try:
            dlq = future.result(timeout=10.0)
        except Exception:
            dlq = []
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._started = False
        logger.info("[SYNC_BRIDGE] Stopped.")
        return dlq

    # -- emit (sync → async) -----------------------------------------------

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
    ) -> bool:
        """Synchronously enqueue an event (thread-safe, blocks until enqueued).

        Returns True if the event was accepted, False if backpressure sent it
        to the Dead-Letter Queue.
        """
        if not self._started or self._loop is None:
            logger.warning(
                "[SYNC_BRIDGE] emit() called but bridge not started. "
                "Falling back to local log."
            )
            return False
        future = asyncio.run_coroutine_threadsafe(
            self._async_bus.emit(event_type, payload, source, priority),
            self._loop,
        )
        try:
            return future.result(timeout=2.0)
        except Exception as exc:
            logger.error(f"[SYNC_BRIDGE] emit failed: {exc}")
            return False

    # -- monitoring proxies -------------------------------------------------

    @property
    def dlq_size(self) -> int:
        return self._async_bus.dlq_size

    @property
    def event_count(self) -> int:
        return self._async_bus.event_count

    @property
    def queue_size(self) -> int:
        return self._async_bus.queue_size

    @property
    def recovery_epoch(self) -> str:
        return self._async_bus._recovery_epoch

    # -- internals ----------------------------------------------------------

    def _run_loop(self) -> None:
        """Run the asyncio event loop in a daemon thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
