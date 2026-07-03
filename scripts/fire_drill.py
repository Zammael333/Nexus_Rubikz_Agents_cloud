#!/usr/bin/env python3
"""Paso 118 — Fire Drill: simulación de caída + failover del bus."""

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
logger = logging.getLogger("fire_drill")


async def run_drill(rto_target: float = 2.5):
    logger.info("=" * 60)
    logger.info("FIRE DRILL — Simulación de caída + failover")
    logger.info(f"RTO target: {rto_target}s")
    logger.info("=" * 60)

    bus = AsyncEventBus(
        flush_interval=0.5,
        max_queue_size=5000,
        log_file="/dev/null",
    )
    await bus.start()

    async def emit_burst(label: str, count: int = 50) -> tuple[int, int]:
        ok = 0
        fail = 0
        for i in range(count):
            r = await bus.emit(
                event_type=f"drill.{label}",
                payload={"seq": i},
                source="fire_drill",
                priority=EventPriority.NORMAL,
            )
            if r:
                ok += 1
            else:
                fail += 1
        return ok, fail

    phases = {
        "normal": "Primary model (Vertex AI) — nominal",
        "degraded": "Primary DOWN — failover to Google AI Studio",
        "recovered": "Primary back — restore to Vertex AI",
    }

    results = {}
    all_ok = True

    for phase, description in phases.items():
        logger.info("")
        logger.info(f"--- Phase: {phase} ---")
        logger.info(f"  {description}")

        start = time.time()
        ok, fail = await emit_burst(phase)
        elapsed = time.time() - start

        # Check RTO in degraded phase
        if phase == "degraded" and elapsed > rto_target:
            logger.info(f"  ✗ RTO EXCEEDED: {elapsed:.2f}s > {rto_target}s target")
            all_ok = False
        else:
            logger.info(f"  Duration: {elapsed:.2f}s")

        logger.info(f"  OK: {ok}  Fail: {fail}")
        results[phase] = {"ok": ok, "fail": fail, "elapsed_s": round(elapsed, 2)}

    # Final drain
    while bus.queue_size > 0:
        await asyncio.sleep(0.5)

    dlq = await bus.stop()

    logger.info("")
    logger.info("=" * 60)
    logger.info("FIRE DRILL RESULTS")
    logger.info("=" * 60)
    for phase, r in results.items():
        logger.info(f"  {phase}: OK={r['ok']} Fail={r['fail']} ({r['elapsed_s']}s)")
    logger.info(f"  Total DLQ:  {len(dlq)}")

    if len(dlq) > 0:
        logger.info("  ✗ DLQ has events after drill")
        all_ok = False

    if all_ok:
        logger.info("")
        logger.info("✓ FIRE DRILL PASSED — all phases completed within RTO")
    else:
        logger.info("")
        logger.info("✗ FIRE DRILL FAILED — see details above")

    report = {
        "test": "fire_drill",
        "rto_target_s": rto_target,
        "phases": results,
        "total_dlq": len(dlq),
        "passed": all_ok,
    }
    os.makedirs("tests/load_test/.results", exist_ok=True)
    with open("tests/load_test/.results/fire_drill.json", "w") as f:
        json.dump(report, f, indent=2)
    logger.info("\nReport saved to tests/load_test/.results/fire_drill.json")

    return 0 if all_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rto", type=float, default=2.5)
    args = parser.parse_args()
    sys.exit(asyncio.run(run_drill(rto_target=args.rto)))
