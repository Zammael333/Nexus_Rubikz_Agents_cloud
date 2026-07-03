#!/usr/bin/env python3
"""Paso 116 — Stress Test: simula carga máxima en el bus asíncrono."""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.bus.async_event_bus import AsyncEventBus, EventPriority

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("stress_test")


@dataclass
class StressResult:
    total_sent: int = 0
    elapsed: float = 0.0
    errors: list[str] = field(default_factory=list)
    final_queue_size: int = 0
    dlq_size: int = 0


async def run_stress_test(
    event_rate: int = 500,
    duration_s: int = 10,
    max_queue_size: int = 10000,
) -> StressResult:
    result = StressResult()
    bus = AsyncEventBus(
        flush_interval=0.5,
        max_queue_size=max_queue_size,
        log_file="/dev/null",
    )
    await bus.start()

    async def producer():
        batch_size = max(1, event_rate // 10)
        deadline = time.time() + duration_s
        while time.time() < deadline:
            for _ in range(batch_size):
                await bus.emit(
                    event_type="stress.event",
                    payload={"seq": result.total_sent, "ts": time.time()},
                    source="stress_test",
                    priority=EventPriority.NORMAL,
                )
                result.total_sent += 1
            await asyncio.sleep(0.1)

    start = time.time()
    await producer()
    result.elapsed = time.time() - start

    while bus.queue_size > 0:
        await asyncio.sleep(0.5)

    dlq = await bus.stop()
    result.dlq_size = len(dlq)
    result.final_queue_size = bus.queue_size

    if result.dlq_size > 0:
        result.errors.append(f"DLQ has {result.dlq_size} events after stress test")
    if bus.event_count != result.total_sent:
        result.errors.append(
            f"event_count mismatch: emitted={result.total_sent} tracked={bus.event_count}"
        )

    return result


async def main():
    event_rate = int(os.environ.get("STRESS_EVENT_RATE", "500"))
    duration = int(os.environ.get("STRESS_DURATION", "10"))
    max_queue = int(os.environ.get("STRESS_MAX_QUEUE", "10000"))

    logger.info("=" * 60)
    logger.info(f"STRESS TEST - {event_rate} ev/s x {duration}s")
    logger.info(f"Max queue size: {max_queue}")
    logger.info("=" * 60)

    result = await run_stress_test(event_rate, duration, max_queue)

    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info(f"  Sent:          {result.total_sent}")
    logger.info(f"  Duration:      {result.elapsed:.2f}s")
    throughput = result.total_sent / result.elapsed if result.elapsed else 0
    logger.info(f"  Throughput:    {throughput:.0f} ev/s")
    logger.info(f"  Final queue:   {result.final_queue_size}")
    logger.info(f"  DLQ size:      {result.dlq_size}")

    if result.errors:
        logger.info("")
        logger.info("ERRORS:")
        for e in result.errors:
            logger.info(f"  ✗ {e}")
        sys.exit(1)
    else:
        logger.info("")
        logger.info("✓ STRESS TEST PASSED — zero loss, all events delivered")

    report = {
        "test": "stress_test",
        "event_rate": event_rate,
        "duration_s": duration,
        "sent": result.total_sent,
        "elapsed_s": round(result.elapsed, 2),
        "throughput_ev_s": round(throughput),
        "final_queue_size": result.final_queue_size,
        "dlq_size": result.dlq_size,
        "passed": len(result.errors) == 0,
    }
    os.makedirs("tests/load_test/.results", exist_ok=True)
    with open("tests/load_test/.results/stress_test.json", "w") as f:
        json.dump(report, f, indent=2)
    logger.info("\nReport saved to tests/load_test/.results/stress_test.json")


if __name__ == "__main__":
    asyncio.run(main())
