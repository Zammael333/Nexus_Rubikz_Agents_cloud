import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.db.connection import AsyncDbPool, DbEngine

logger = logging.getLogger(__name__)


@dataclass
class WorkerStateRecord:
    worker_id: str
    worker_type: str = "generic"
    status: str = "HEALTHY"
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    error_budget_consumed: float = 0.0
    slo_real: float = 1.0
    trust_score: float = 1.0
    last_heartbeat: str = ""
    recovery_epoch: str = ""
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EventLogRecord:
    event_uuid: str
    event_type: str
    source: str = ""
    payload: dict[str, Any] = None
    priority: str = "NORMAL"
    status: str = "PROCESSED"
    error_message: str = ""
    dlq_reason: str = ""
    recovery_epoch: str = ""

    def __post_init__(self) -> None:
        if self.payload is None:
            self.payload = {}


@dataclass
class BudgetSnapshotRecord:
    worker_id: str = "__global__"
    total_requests: int = 0
    total_failures: int = 0
    error_rate: float = 0.0
    budget_consumed: float = 0.0
    slo_target: float = 0.999973
    status: str = "NOMINAL"


@dataclass
class ScorpionFindingRecord:
    scan_id: str
    vector_id: str
    worker_id: str = ""
    severity: str = "MEDIUM"
    description: str = ""
    mitigated: bool = False


class WorkerStateRepo:
    def __init__(self, pool: AsyncDbPool):
        self._pool = pool

    async def upsert(self, record: WorkerStateRecord) -> None:
        now = datetime.now(UTC).isoformat()
        meta_json = json.dumps(record.metadata)
        async with self._pool.acquire() as conn:
            if conn is None:
                return
            if self._pool.engine == DbEngine.SQLITE:
                await conn.execute(
                    """INSERT INTO worker_state
                       (worker_id, worker_type, status, consecutive_failures,
                        total_requests, total_failures, error_budget_consumed,
                        slo_real, trust_score, last_heartbeat, recovery_epoch,
                        metadata_json, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(worker_id) DO UPDATE SET
                           status=excluded.status,
                           consecutive_failures=excluded.consecutive_failures,
                           total_requests=excluded.total_requests,
                           total_failures=excluded.total_failures,
                           error_budget_consumed=excluded.error_budget_consumed,
                           slo_real=excluded.slo_real,
                           trust_score=excluded.trust_score,
                           last_heartbeat=excluded.last_heartbeat,
                           recovery_epoch=excluded.recovery_epoch,
                           metadata_json=excluded.metadata_json,
                           updated_at=excluded.updated_at""",
                    (
                        record.worker_id,
                        record.worker_type,
                        record.status,
                        record.consecutive_failures,
                        record.total_requests,
                        record.total_failures,
                        record.error_budget_consumed,
                        record.slo_real,
                        record.trust_score,
                        record.last_heartbeat,
                        record.recovery_epoch,
                        meta_json,
                        now,
                    ),
                )
            else:
                await conn.execute(
                    """INSERT INTO worker_state
                       (worker_id, worker_type, status, consecutive_failures,
                        total_requests, total_failures, error_budget_consumed,
                        slo_real, trust_score, last_heartbeat, recovery_epoch,
                        metadata_json, updated_at)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13)
                       ON CONFLICT(worker_id) DO UPDATE SET
                           status=EXCLUDED.status,
                           consecutive_failures=EXCLUDED.consecutive_failures,
                           total_requests=EXCLUDED.total_requests,
                           total_failures=EXCLUDED.total_failures,
                           error_budget_consumed=EXCLUDED.error_budget_consumed,
                           slo_real=EXCLUDED.slo_real,
                           trust_score=EXCLUDED.trust_score,
                           last_heartbeat=EXCLUDED.last_heartbeat,
                           recovery_epoch=EXCLUDED.recovery_epoch,
                           metadata_json=EXCLUDED.metadata_json,
                           updated_at=EXCLUDED.updated_at""",
                    (
                        record.worker_id,
                        record.worker_type,
                        record.status,
                        record.consecutive_failures,
                        record.total_requests,
                        record.total_failures,
                        record.error_budget_consumed,
                        record.slo_real,
                        record.trust_score,
                        record.last_heartbeat,
                        record.recovery_epoch,
                        meta_json,
                        now,
                    ),
                )

    async def get(self, worker_id: str) -> WorkerStateRecord | None:
        async with self._pool.acquire() as conn:
            if conn is None:
                return None
            if self._pool.engine == DbEngine.SQLITE:
                cursor = await conn.execute(
                    "SELECT * FROM worker_state WHERE worker_id = ?",
                    (worker_id,),
                )
                row = await cursor.fetchone()
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM worker_state WHERE worker_id = $1",
                    (worker_id,),
                )
            if row is None:
                return None
            return self._row_to_record(row)

    async def list_all(self) -> list[WorkerStateRecord]:
        async with self._pool.acquire() as conn:
            if conn is None:
                return []
            if self._pool.engine == DbEngine.SQLITE:
                cursor = await conn.execute(
                    "SELECT * FROM worker_state ORDER BY worker_id"
                )
                rows = await cursor.fetchall()
            else:
                rows = await conn.fetch("SELECT * FROM worker_state ORDER BY worker_id")
            return [self._row_to_record(r) for r in rows]

    async def delete(self, worker_id: str) -> bool:
        async with self._pool.acquire() as conn:
            if conn is None:
                return False
            if self._pool.engine == DbEngine.SQLITE:
                cursor = await conn.execute(
                    "DELETE FROM worker_state WHERE worker_id = ?",
                    (worker_id,),
                )
                return cursor.rowcount > 0
            result = await conn.execute(
                "DELETE FROM worker_state WHERE worker_id = $1",
                (worker_id,),
            )
            return result > 0

    def _row_to_record(self, row) -> WorkerStateRecord:
        if hasattr(row, "keys"):
            d = dict(row)
        else:
            d = dict(row)
        meta_raw = d.get("metadata_json", "{}")
        return WorkerStateRecord(
            worker_id=d["worker_id"],
            worker_type=d.get("worker_type", "generic"),
            status=d.get("status", "HEALTHY"),
            consecutive_failures=d.get("consecutive_failures", 0),
            total_requests=d.get("total_requests", 0),
            total_failures=d.get("total_failures", 0),
            error_budget_consumed=float(d.get("error_budget_consumed", 0.0)),
            slo_real=float(d.get("slo_real", 1.0)),
            trust_score=float(d.get("trust_score", 1.0)),
            last_heartbeat=d.get("last_heartbeat", ""),
            recovery_epoch=d.get("recovery_epoch", ""),
            metadata=json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw,
        )


class EventLogRepo:
    def __init__(self, pool: AsyncDbPool):
        self._pool = pool

    async def insert(self, record: EventLogRecord) -> None:
        payload_json = json.dumps(record.payload)
        async with self._pool.acquire() as conn:
            if conn is None:
                return
            if self._pool.engine == DbEngine.SQLITE:
                await conn.execute(
                    """INSERT INTO event_log
                       (event_uuid, event_type, source, payload_json,
                        priority, status, error_message, dlq_reason, recovery_epoch)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.event_uuid,
                        record.event_type,
                        record.source,
                        payload_json,
                        record.priority,
                        record.status,
                        record.error_message,
                        record.dlq_reason,
                        record.recovery_epoch,
                    ),
                )
            else:
                await conn.execute(
                    """INSERT INTO event_log
                       (event_uuid, event_type, source, payload_json,
                        priority, status, error_message, dlq_reason, recovery_epoch)
                       VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9)""",
                    (
                        record.event_uuid,
                        record.event_type,
                        record.source,
                        payload_json,
                        record.priority,
                        record.status,
                        record.error_message,
                        record.dlq_reason,
                        record.recovery_epoch,
                    ),
                )

    async def list_recent(
        self, limit: int = 100, offset: int = 0
    ) -> list[EventLogRecord]:
        async with self._pool.acquire() as conn:
            if conn is None:
                return []
            if self._pool.engine == DbEngine.SQLITE:
                cursor = await conn.execute(
                    "SELECT * FROM event_log ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
                rows = await cursor.fetchall()
            else:
                rows = await conn.fetch(
                    "SELECT * FROM event_log ORDER BY id DESC LIMIT $1 OFFSET $2",
                    (limit, offset),
                )
            return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row) -> EventLogRecord:
        if hasattr(row, "keys"):
            d = dict(row)
        else:
            d = dict(row)
        payload_raw = d.get("payload_json", "{}")
        return EventLogRecord(
            event_uuid=d["event_uuid"],
            event_type=d["event_type"],
            source=d.get("source", ""),
            payload=json.loads(payload_raw)
            if isinstance(payload_raw, str)
            else payload_raw,
            priority=d.get("priority", "NORMAL"),
            status=d.get("status", "PROCESSED"),
            error_message=d.get("error_message", ""),
            dlq_reason=d.get("dlq_reason", ""),
            recovery_epoch=d.get("recovery_epoch", ""),
        )


class BudgetSnapshotRepo:
    def __init__(self, pool: AsyncDbPool):
        self._pool = pool

    async def insert(self, record: BudgetSnapshotRecord) -> None:
        async with self._pool.acquire() as conn:
            if conn is None:
                return
            if self._pool.engine == DbEngine.SQLITE:
                await conn.execute(
                    """INSERT INTO budget_snapshots
                       (worker_id, total_requests, total_failures, error_rate,
                        budget_consumed, slo_target, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.worker_id,
                        record.total_requests,
                        record.total_failures,
                        record.error_rate,
                        record.budget_consumed,
                        record.slo_target,
                        record.status,
                    ),
                )
            else:
                await conn.execute(
                    """INSERT INTO budget_snapshots
                       (worker_id, total_requests, total_failures, error_rate,
                        budget_consumed, slo_target, status)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    (
                        record.worker_id,
                        record.total_requests,
                        record.total_failures,
                        record.error_rate,
                        record.budget_consumed,
                        record.slo_target,
                        record.status,
                    ),
                )

    async def list_recent(
        self, worker_id: str = "", limit: int = 50
    ) -> list[BudgetSnapshotRecord]:
        async with self._pool.acquire() as conn:
            if conn is None:
                return []
            if self._pool.engine == DbEngine.SQLITE:
                if worker_id:
                    cursor = await conn.execute(
                        "SELECT * FROM budget_snapshots WHERE worker_id = ? ORDER BY id DESC LIMIT ?",
                        (worker_id, limit),
                    )
                else:
                    cursor = await conn.execute(
                        "SELECT * FROM budget_snapshots ORDER BY id DESC LIMIT ?",
                        (limit,),
                    )
                rows = await cursor.fetchall()
            else:
                if worker_id:
                    rows = await conn.fetch(
                        "SELECT * FROM budget_snapshots WHERE worker_id = $1 ORDER BY id DESC LIMIT $2",
                        (worker_id, limit),
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM budget_snapshots ORDER BY id DESC LIMIT $1",
                        (limit,),
                    )
            return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row) -> BudgetSnapshotRecord:
        if hasattr(row, "keys"):
            d = dict(row)
        else:
            d = dict(row)
        return BudgetSnapshotRecord(
            worker_id=d.get("worker_id", "__global__"),
            total_requests=d.get("total_requests", 0),
            total_failures=d.get("total_failures", 0),
            error_rate=float(d.get("error_rate", 0.0)),
            budget_consumed=float(d.get("budget_consumed", 0.0)),
            slo_target=float(d.get("slo_target", 0.999973)),
            status=d.get("status", "NOMINAL"),
        )


class ScorpionFindingRepo:
    def __init__(self, pool: AsyncDbPool):
        self._pool = pool

    async def insert(self, record: ScorpionFindingRecord) -> None:
        async with self._pool.acquire() as conn:
            if conn is None:
                return
            if self._pool.engine == DbEngine.SQLITE:
                await conn.execute(
                    """INSERT INTO scorpion_findings
                       (scan_id, worker_id, vector_id, severity, description, mitigated)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        record.scan_id,
                        record.worker_id,
                        record.vector_id,
                        record.severity,
                        record.description,
                        1 if record.mitigated else 0,
                    ),
                )
            else:
                await conn.execute(
                    """INSERT INTO scorpion_findings
                       (scan_id, worker_id, vector_id, severity, description, mitigated)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    (
                        record.scan_id,
                        record.worker_id,
                        record.vector_id,
                        record.severity,
                        record.description,
                        record.mitigated,
                    ),
                )

    async def list_unmitigated(self) -> list[ScorpionFindingRecord]:
        async with self._pool.acquire() as conn:
            if conn is None:
                return []
            if self._pool.engine == DbEngine.SQLITE:
                cursor = await conn.execute(
                    "SELECT * FROM scorpion_findings WHERE mitigated = 0 ORDER BY id DESC"
                )
                rows = await cursor.fetchall()
            else:
                rows = await conn.fetch(
                    "SELECT * FROM scorpion_findings WHERE mitigated = FALSE ORDER BY id DESC"
                )
            return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row) -> ScorpionFindingRecord:
        if hasattr(row, "keys"):
            d = dict(row)
        else:
            d = dict(row)
        return ScorpionFindingRecord(
            scan_id=d["scan_id"],
            worker_id=d.get("worker_id", ""),
            vector_id=d["vector_id"],
            severity=d.get("severity", "MEDIUM"),
            description=d.get("description", ""),
            mitigated=bool(d.get("mitigated", False)),
        )
