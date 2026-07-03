#!/usr/bin/env python3
"""Paso 117 — Verificación de SLO 99.9973% bajo carga."""

import argparse
import asyncio
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.bus.async_event_bus import AsyncEventBus, EventPriority

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("slo_verify")

SLO_TARGET = 99.9973
ERROR_BUDGET_MAX = 0.0027
TOTAL_REQUESTS_TARGET = 100_000


async def verify():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=TOTAL_REQUESTS_TARGET)
    parser.add_argument("--concurrency", type=int, default=100)
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"SLO VERIFICATION — Target: {SLO_TARGET}%")
    logger.info(f"Error Budget Max: {ERROR_BUDGET_MAX}%")
    logger.info(f"Total requests:   {args.requests}")
    logger.info(f"Concurrency:      {args.concurrency}")
    logger.info("=" * 60)

    bus = AsyncEventBus(
        flush_interval=0.2,
        max_queue_size=args.requests * 2,
        log_file="/dev/null",
    )
    await bus.start()

    failures = 0

    async def worker(n: int):
        nonlocal failures
        for i in range(n):
            ok = await bus.emit(
                event_type="slo.verify",
                payload={"seq": i, "ts": time.time()},
                source="slo_verify",
                priority=EventPriority.NORMAL,
            )
            if not ok:
                failures += 1

    batch = args.requests // args.concurrency
    tasks = [asyncio.create_task(worker(batch)) for _ in range(args.concurrency - 1)]
    remainder = args.requests - batch * (args.concurrency - 1)
    tasks.append(asyncio.create_task(worker(remainder)))

    start = time.time()
    await asyncio.gather(*tasks)

    while bus.queue_size > 0:
        await asyncio.sleep(0.5)

    dlq = await bus.stop()
    total = bus.event_count
    dlq_failures = len(dlq)
    total_failures = failures + dlq_failures
    elapsed = time.time() - start
    success_rate = ((total - total_failures) / total * 100) if total > 0 else 0.0

    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    logger.info(f"  Total attempted:     {args.requests}")
    logger.info(f"  Total tracked:       {total}")
    logger.info(f"  Emit failures:       {failures}")
    logger.info(f"  DLQ after drain:     {dlq_failures}")
    logger.info(f"  Total failures:      {total_failures}")
    logger.info(f"  Duration:            {elapsed:.2f}s")
    logger.info(f"  Success rate:        {success_rate:.6f}%")
    logger.info(f"  Target:              {SLO_TARGET}%")

    met = success_rate >= SLO_TARGET
    if met:
        logger.info("")
        logger.info("✓ SLO VERIFICATION PASSED — Success rate meets 99.9973% target")
    else:
        logger.info("")
        logger.info(f"✗ SLO VERIFICATION FAILED — {success_rate:.4f}% < {SLO_TARGET}%")

    if failures > 0:
        logger.info(f"\n  Note: {failures} immediate emit failures detected")

    report = {
        "test": "slo_verify",
        "target": SLO_TARGET,
        "total_attempted": args.requests,
        "total_tracked": total,
        "emit_failures": failures,
        "dlq_failures": dlq_failures,
        "total_failures": total_failures,
        "elapsed_s": round(elapsed, 2),
        "success_rate": round(success_rate, 6),
        "met": met,
    }
    os.makedirs("tests/load_test/.results", exist_ok=True)
    with open("tests/load_test/.results/slo_verify.json", "w") as f:
        json.dump(report, f, indent=2)
    logger.info("\nReport saved to tests/load_test/.results/slo_verify.json")

    return 0 if met else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(verify()))
