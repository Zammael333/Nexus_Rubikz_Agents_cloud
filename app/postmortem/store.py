from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    import aiosqlite

    _AIO_SQLITE_AVAILABLE = True
except ImportError:
    _AIO_SQLITE_AVAILABLE = False


@dataclass
class IncidentRecord:
    worker_id: str
    error_message: str
    error_fingerprint: str
    severity: str = "error"
    context: dict[str, Any] = field(default_factory=dict)
    resolution: str = ""
    resolved_at: str = ""
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "worker_id": self.worker_id,
            "error_message": self.error_message,
            "error_fingerprint": self.error_fingerprint,
            "severity": self.severity,
            "context": dict(self.context),
            "resolution": self.resolution,
            "resolved_at": self.resolved_at,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> IncidentRecord:
        return IncidentRecord(
            worker_id=data["worker_id"],
            error_message=data["error_message"],
            error_fingerprint=data["error_fingerprint"],
            severity=data.get("severity", "error"),
            context=dict(data.get("context", {})),
            resolution=data.get("resolution", ""),
            resolved_at=data.get("resolved_at", ""),
            incident_id=data.get("incident_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now(UTC).isoformat()),
        )


def fingerprint_error(error_message: str) -> str:
    return hashlib.sha256(error_message.encode()).hexdigest()[:16]


class PostmortemStore:
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn: Any = None
        self._records: dict[str, IncidentRecord] = {}
        self._use_sqlite = _AIO_SQLITE_AVAILABLE and db_path != ":memory:"

    async def initialize(self) -> None:
        if self._use_sqlite:
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_fingerprint TEXT NOT NULL,
                    severity TEXT DEFAULT 'error',
                    context TEXT DEFAULT '{}',
                    resolution TEXT DEFAULT '',
                    resolved_at TEXT DEFAULT '',
                    timestamp TEXT NOT NULL
                )
            """)
            await self._conn.commit()
            logger.info(f"[POSTMORTEM] SQLite store initialized: {self._db_path}")
        else:
            logger.info(
                f"[POSTMORTEM] In-memory store initialized"
                f"{' (SQLite unavailable)' if not _AIO_SQLITE_AVAILABLE else ''}"
            )

    async def store(self, incident: IncidentRecord) -> str:
        if self._use_sqlite and self._conn:
            await self._conn.execute(
                """INSERT OR REPLACE INTO incidents
                   (incident_id, worker_id, error_message, error_fingerprint,
                    severity, context, resolution, resolved_at, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    incident.incident_id,
                    incident.worker_id,
                    incident.error_message,
                    incident.error_fingerprint,
                    incident.severity,
                    json.dumps(incident.context),
                    incident.resolution,
                    incident.resolved_at,
                    incident.timestamp,
                ),
            )
            await self._conn.commit()
        self._records[incident.incident_id] = incident
        return incident.incident_id

    async def find_similar(
        self, error_fingerprint: str, worker_id: str | None = None
    ) -> list[IncidentRecord]:
        results: list[IncidentRecord] = []
        for record in self._records.values():
            if record.error_fingerprint == error_fingerprint:
                if worker_id and record.worker_id != worker_id:
                    continue
                results.append(record)
        if self._use_sqlite and self._conn and not results:
            cursor = await self._conn.execute(
                "SELECT * FROM incidents WHERE error_fingerprint = ?"
                + (" AND worker_id = ?" if worker_id else ""),
                (error_fingerprint, worker_id) if worker_id else (error_fingerprint,),
            )
            rows = await cursor.fetchall()
            for row in rows:
                results.append(self._row_to_record(row))
        return results

    async def find_by_worker(self, worker_id: str) -> list[IncidentRecord]:
        return [r for r in self._records.values() if r.worker_id == worker_id]

    async def list_recent(self, limit: int = 10) -> list[IncidentRecord]:
        sorted_records = sorted(
            self._records.values(),
            key=lambda r: r.timestamp,
            reverse=True,
        )
        return sorted_records[:limit]

    async def resolve(self, incident_id: str, resolution: str) -> bool:
        record = self._records.get(incident_id)
        if record is None:
            return False
        record.resolution = resolution
        record.resolved_at = datetime.now(UTC).isoformat()
        if self._use_sqlite and self._conn:
            await self._conn.execute(
                "UPDATE incidents SET resolution = ?, resolved_at = ? WHERE incident_id = ?",
                (resolution, record.resolved_at, incident_id),
            )
            await self._conn.commit()
        return True

    async def count_recurrences(
        self, error_fingerprint: str, worker_id: str | None = None
    ) -> int:
        similar = await self.find_similar(error_fingerprint, worker_id)
        return len(similar)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    def _row_to_record(self, row: tuple) -> IncidentRecord:
        return IncidentRecord(
            incident_id=row[0],
            worker_id=row[1],
            error_message=row[2],
            error_fingerprint=row[3],
            severity=row[4],
            context=json.loads(row[5]) if row[5] else {},
            resolution=row[6],
            resolved_at=row[7],
            timestamp=row[8],
        )

    @property
    def total_incidents(self) -> int:
        return len(self._records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_incidents": self.total_incidents,
            "db_path": self._db_path,
            "use_sqlite": self._use_sqlite,
            "recent": [
                r.to_dict()
                for r in sorted(
                    self._records.values(),
                    key=lambda x: x.timestamp,
                    reverse=True,
                )[:10]
            ],
        }
