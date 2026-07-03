from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TwinSnapshot:
    worker_id: str
    status: str
    state: dict[str, Any]
    trust_score: float | None = None
    spiffe_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "state": dict(self.state),
            "trust_score": self.trust_score,
            "spiffe_id": self.spiffe_id,
            "timestamp": self.timestamp,
        }


StateProvider = Any


class DigitalTwinEmitter:
    def __init__(self, poll_interval: float = 5.0) -> None:
        self._providers: dict[str, StateProvider] = {}
        self._mirror: dict[str, TwinSnapshot] = {}
        self._poll_interval = poll_interval
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._callbacks: list[Any] = []
        self._background_tasks: set[asyncio.Task] = set()

    def register_provider(self, worker_id: str, provider: StateProvider) -> None:
        self._providers[worker_id] = provider
        logger.info(f"[TWIN] Provider registered: {worker_id}")

    def unregister_provider(self, worker_id: str) -> None:
        self._providers.pop(worker_id, None)
        self._mirror.pop(worker_id, None)

    def register_callback(self, callback: Any) -> None:
        self._callbacks.append(callback)

    async def poll_once(self) -> list[TwinSnapshot]:
        snapshots: list[TwinSnapshot] = []
        for worker_id, provider in list(self._providers.items()):
            try:
                if asyncio.iscoroutinefunction(provider):
                    state = await provider()
                else:
                    state = provider()
                snapshot = TwinSnapshot(
                    worker_id=worker_id,
                    status=state.get("status", "unknown"),
                    state=state.get("data", {}),
                    trust_score=state.get("trust_score"),
                    spiffe_id=state.get("spiffe_id", ""),
                )
            except Exception as e:
                snapshot = TwinSnapshot(
                    worker_id=worker_id,
                    status="error",
                    state={"error": str(e)},
                )
            self._mirror[worker_id] = snapshot
            snapshots.append(snapshot)
            for cb in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        self._background_tasks.add(asyncio.create_task(cb(snapshot)))
                    else:
                        cb(snapshot)
                except Exception:
                    logger.exception(f"[TWIN] Callback failed for {worker_id}")
        return snapshots

    def get_snapshot(self, worker_id: str) -> TwinSnapshot | None:
        return self._mirror.get(worker_id)

    def get_all_snapshots(self) -> dict[str, TwinSnapshot]:
        return dict(self._mirror)

    def get_drift(self, worker_id: str) -> float:
        snapshot = self._mirror.get(worker_id)
        if snapshot is None or snapshot.trust_score is None:
            return 1.0
        trust = snapshot.trust_score
        return abs(1.0 - trust)

    def count_drifted(self, threshold: float = 0.05) -> int:
        return sum(1 for wid in self._mirror if self.get_drift(wid) > threshold)

    @property
    def mirror_size(self) -> int:
        return len(self._mirror)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.poll_once()
            except Exception:
                logger.exception("[TWIN] Poll cycle failed")
            await asyncio.sleep(self._poll_interval)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mirror": {wid: snap.to_dict() for wid, snap in self._mirror.items()},
            "poll_interval": self._poll_interval,
            "running": self._running,
        }
