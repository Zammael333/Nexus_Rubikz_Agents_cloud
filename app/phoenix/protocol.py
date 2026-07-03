from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.repository import WorkerStateRepo

from app.config import settings
from app.db.repository import WorkerStateRecord

logger = logging.getLogger(__name__)

RTO_TARGET_SECONDS = settings.phoenix_rto_target_seconds
HEALTH_CHECK_INTERVAL = settings.phoenix_health_check_interval
MAX_CONSECUTIVE_FAILURES = settings.phoenix_max_consecutive_failures
QUARANTINE_THRESHOLD = settings.phoenix_quarantine_threshold
QUARANTINE_WINDOW_SECONDS = settings.phoenix_quarantine_window_seconds


class WorkerStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    QUARANTINED = "quarantined"


@dataclass
class HealthReport:
    worker_id: str
    status: WorkerStatus
    latency_ms: float
    last_heartbeat: str
    consecutive_failures: int
    recovery_count: int
    recovery_epoch: str


@dataclass
class WorkerRecord:
    name: str
    health_check_fn: Callable[[], bool]
    status: WorkerStatus = WorkerStatus.HEALTHY
    consecutive_failures: int = 0
    recovery_count: int = 0
    recovery_epoch: str = field(default_factory=lambda: str(uuid.uuid4()))
    last_heartbeat: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_recovery_time: float = 0.0
    first_failure_in_window: float = 0.0


class PhoenixProtocol:
    def __init__(
        self,
        rto_target: float = RTO_TARGET_SECONDS,
        health_interval: float = HEALTH_CHECK_INTERVAL,
        max_failures: int = MAX_CONSECUTIVE_FAILURES,
        quarantine_threshold: int = QUARANTINE_THRESHOLD,
        quarantine_window: float = QUARANTINE_WINDOW_SECONDS,
        on_recovery: Callable[[str, str], None] | None = None,
        on_quarantine: Callable[[str], None] | None = None,
        repo: WorkerStateRepo | None = None,
    ):
        self.rto_target = rto_target
        self.health_interval = health_interval
        self.max_failures = max_failures
        self.quarantine_threshold = quarantine_threshold
        self.quarantine_window = quarantine_window
        self.on_recovery = on_recovery
        self.on_quarantine = on_quarantine
        self._repo = repo
        self._workers: dict[str, WorkerRecord] = {}
        self._running = False
        self._monitor_task: asyncio.Task | None = None
        self._background_tasks: set[asyncio.Task] = set()

    def register(self, name: str, health_check_fn: Callable[[], bool]) -> None:
        self._workers[name] = WorkerRecord(name=name, health_check_fn=health_check_fn)
        logger.info(f"[PHOENIX] Worker '{name}' registered.")

    async def _persist(self, name: str) -> None:
        if self._repo is None:
            return
        worker = self._workers.get(name)
        if worker is None:
            return
        record = WorkerStateRecord(
            worker_id=name,
            status=worker.status.value,
            consecutive_failures=worker.consecutive_failures,
            last_heartbeat=worker.last_heartbeat,
            recovery_epoch=worker.recovery_epoch,
        )
        await self._repo.upsert(record)

    def _schedule_persist(self, name: str) -> None:
        try:
            self._background_tasks.add(asyncio.create_task(self._persist(name)))
        except RuntimeError:
            pass

    def unregister(self, name: str) -> None:
        self._workers.pop(name, None)
        logger.info(f"[PHOENIX] Worker '{name}' unregistered.")

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"[PHOENIX] Monitor started (RTO target: {self.rto_target}s).")

    async def stop(self) -> None:
        self._running = False
        if self._monitor_task:
            try:
                await asyncio.wait_for(self._monitor_task, timeout=5.0)
            except TimeoutError:
                logger.warning("[PHOENIX] Monitor did not stop cleanly.")

    async def _monitor_loop(self) -> None:
        while self._running:
            now = time.time()
            for worker in list(self._workers.values()):
                await self._check_worker(worker, now)
            await asyncio.sleep(self.health_interval)

    async def _check_worker(self, worker: WorkerRecord, now: float) -> None:
        start = time.perf_counter()
        try:
            healthy = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, worker.health_check_fn),
                timeout=self.rto_target,
            )
        except (TimeoutError, Exception) as e:
            healthy = False
            logger.warning(f"[PHOENIX] Health check failed for '{worker.name}': {e}")

        latency = (time.perf_counter() - start) * 1000
        worker.last_heartbeat = datetime.now(UTC).isoformat()

        if healthy:
            if worker.status in (WorkerStatus.FAILED, WorkerStatus.RECOVERING):
                self._recover_worker(worker, latency)
            else:
                worker.status = WorkerStatus.HEALTHY
                worker.consecutive_failures = 0
        else:
            worker.consecutive_failures += 1
            if worker.consecutive_failures == 1:
                worker.first_failure_in_window = now
                worker.status = WorkerStatus.DEGRADED
            elif worker.consecutive_failures >= self.max_failures:
                worker.status = WorkerStatus.FAILED
                self._handle_failure(worker, now)
        await self._persist(worker.name)

    def _recover_worker(self, worker: WorkerRecord, latency: float) -> None:
        worker.recovery_count += 1
        worker.recovery_epoch = str(uuid.uuid4())
        worker.consecutive_failures = 0
        worker.status = WorkerStatus.HEALTHY
        worker.last_recovery_time = time.time()
        rto_met = latency / 1000 <= self.rto_target
        logger.info(
            f"[PHOENIX] Worker '{worker.name}' recovered. "
            f"Latency: {latency:.1f}ms. RTO {'MET' if rto_met else 'EXCEEDED'}."
        )
        if self.on_recovery:
            self.on_recovery(worker.name, worker.recovery_epoch)

    def _handle_failure(self, worker: WorkerRecord, now: float) -> None:
        window_failures = sum(
            1
            for w in self._workers.values()
            if w.status == WorkerStatus.FAILED
            and now - w.last_recovery_time < self.quarantine_window
        )
        if window_failures >= self.quarantine_threshold:
            worker.status = WorkerStatus.QUARANTINED
            logger.error(
                f"[PHOENIX] Worker '{worker.name}' QUARANTINED "
                f"({window_failures} failures in {self.quarantine_window}s)."
            )
            if self.on_quarantine:
                self.on_quarantine(worker.name)

    def force_recovery(self, worker_name: str) -> bool:
        worker = self._workers.get(worker_name)
        if not worker:
            return False
        worker.recovery_epoch = str(uuid.uuid4())
        worker.consecutive_failures = 0
        worker.status = WorkerStatus.HEALTHY
        worker.last_recovery_time = time.time()
        logger.info(f"[PHOENIX] Manual recovery triggered for '{worker_name}'.")
        self._schedule_persist(worker_name)
        return True

    def get_report(self, worker_name: str) -> HealthReport | None:
        worker = self._workers.get(worker_name)
        if not worker:
            return None
        return HealthReport(
            worker_id=worker.name,
            status=worker.status,
            latency_ms=0.0,
            last_heartbeat=worker.last_heartbeat,
            consecutive_failures=worker.consecutive_failures,
            recovery_count=worker.recovery_count,
            recovery_epoch=worker.recovery_epoch,
        )

    def get_all_reports(self) -> dict[str, HealthReport]:
        return {
            name: self.get_report(name)
            for name in self._workers
            if self.get_report(name) is not None
        }
