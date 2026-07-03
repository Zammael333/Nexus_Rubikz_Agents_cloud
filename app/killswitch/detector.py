from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RecursionRecord:
    source_worker: str
    target_worker: str
    action: str
    count: int
    first_seen: str
    last_seen: str
    cutoff: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_worker": self.source_worker,
            "target_worker": self.target_worker,
            "action": self.action,
            "count": self.count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "cutoff": self.cutoff,
        }


class RecursionDetector:
    def __init__(
        self,
        max_depth: int = 5,
        max_count: int = 10,
        window_seconds: float = 60.0,
    ) -> None:
        self._max_depth = max_depth
        self._max_count = max_count
        self._window_seconds = window_seconds
        self._invocations: dict[str, list[float]] = defaultdict(list)
        self._cutoff: dict[str, bool] = {}
        self._records: dict[str, RecursionRecord] = {}
        self._history: list[RecursionRecord] = []

    def _key(self, source: str | None, target: str, action: str) -> str:
        return f"{source or 'unknown'}:{target}:{action}"

    def _prune(self) -> None:
        now = time.time()
        for key in list(self._invocations):
            self._invocations[key] = [
                t for t in self._invocations[key] if now - t < self._window_seconds
            ]
            if not self._invocations[key]:
                del self._invocations[key]

    def record_invocation(
        self, target: str, action: str, source: str | None = None
    ) -> RecursionRecord:
        self._prune()
        key = self._key(source, target, action)
        now_iso = datetime.now(UTC).isoformat()
        now_ts = time.time()

        self._invocations[key].append(now_ts)
        count = len(self._invocations[key])

        depth = self._compute_depth(source or "", target, action)

        if key not in self._records:
            self._records[key] = RecursionRecord(
                source_worker=source or "",
                target_worker=target,
                action=action,
                count=count,
                first_seen=now_iso,
                last_seen=now_iso,
                cutoff=False,
            )
        else:
            self._records[key].count = count
            self._records[key].last_seen = now_iso

        if depth >= self._max_depth or count >= self._max_count:
            self._cutoff[key] = True
            self._records[key].cutoff = True

        return self._records[key]

    def _compute_depth(self, source: str, target: str, action: str) -> int:
        visited: set[str] = set()
        stack = [(source, 0)]
        while stack:
            worker, d = stack.pop()
            if worker in visited:
                continue
            visited.add(worker)
            if worker == target:
                return d + 1
            nxt = f"{worker}:{target}:{action}"
            if self._cutoff.get(nxt):
                continue
            if d < self._max_depth:
                stack.append((target, d + 1))
        return 0

    def is_cutoff(self, target: str, action: str, source: str | None = None) -> bool:
        key = self._key(source, target, action)
        return self._cutoff.get(key, False)

    def reset_cutoff(self, target: str, action: str, source: str | None = None) -> None:
        key = self._key(source, target, action)
        self._cutoff.pop(key, None)
        self._invocations.pop(key, None)

    def reset_all(self) -> None:
        self._invocations.clear()
        self._cutoff.clear()
        self._records.clear()

    @property
    def active_cutoffs(self) -> list[RecursionRecord]:
        return [r for r in self._records.values() if r.cutoff]

    @property
    def all_records(self) -> list[RecursionRecord]:
        return list(self._records.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_depth": self._max_depth,
            "max_count": self._max_count,
            "window_seconds": self._window_seconds,
            "active_cutoffs": len(self.active_cutoffs),
            "records": [r.to_dict() for r in self._records.values()],
        }

    @property
    def max_depth(self) -> int:
        return self._max_depth

    @property
    def max_count(self) -> int:
        return self._max_count
