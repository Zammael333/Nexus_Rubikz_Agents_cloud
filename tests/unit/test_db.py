import os
import tempfile

import pytest
import pytest_asyncio

from app.db.connection import AsyncDbPool, CloudSqlConfig
from app.db.migrations import ensure_schema
from app.db.repository import (
    BudgetSnapshotRecord,
    BudgetSnapshotRepo,
    EventLogRecord,
    EventLogRepo,
    ScorpionFindingRecord,
    ScorpionFindingRepo,
    WorkerStateRecord,
    WorkerStateRepo,
)


@pytest_asyncio.fixture
async def pool():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    config = CloudSqlConfig(dsn=f"sqlite:///{tmp.name}")
    p = AsyncDbPool(config)
    await p.start()
    await ensure_schema(p)
    yield p
    await p.close()
    os.unlink(tmp.name)


@pytest.mark.asyncio
async def test_pool_starts_sqlite(pool):
    from app.db.connection import DbEngine

    assert pool.engine == DbEngine.SQLITE
    assert pool.is_connected
    stats = pool.stats
    assert stats.engine == DbEngine.SQLITE


@pytest.mark.asyncio
async def test_worker_state_upsert_and_get(pool):
    repo = WorkerStateRepo(pool)
    rec = WorkerStateRecord(
        worker_id="test-worker-1",
        worker_type="budget_watchdog",
        status="HEALTHY",
        trust_score=0.95,
        metadata={"version": "1.0"},
    )
    await repo.upsert(rec)

    fetched = await repo.get("test-worker-1")
    assert fetched is not None
    assert fetched.worker_id == "test-worker-1"
    assert fetched.status == "HEALTHY"
    assert fetched.trust_score == 0.95
    assert fetched.metadata == {"version": "1.0"}


@pytest.mark.asyncio
async def test_worker_state_upsert_updates_existing(pool):
    repo = WorkerStateRepo(pool)
    rec = WorkerStateRecord(worker_id="w1", status="HEALTHY", total_requests=10)
    await repo.upsert(rec)

    rec2 = WorkerStateRecord(worker_id="w1", status="DEGRADED", total_requests=20)
    await repo.upsert(rec2)

    fetched = await repo.get("w1")
    assert fetched is not None
    assert fetched.status == "DEGRADED"
    assert fetched.total_requests == 20


@pytest.mark.asyncio
async def test_worker_state_list_all(pool):
    repo = WorkerStateRepo(pool)
    await repo.upsert(WorkerStateRecord(worker_id="w1"))
    await repo.upsert(WorkerStateRecord(worker_id="w2"))

    all_workers = await repo.list_all()
    assert len(all_workers) == 2
    ids = {w.worker_id for w in all_workers}
    assert ids == {"w1", "w2"}


@pytest.mark.asyncio
async def test_worker_state_delete(pool):
    repo = WorkerStateRepo(pool)
    await repo.upsert(WorkerStateRecord(worker_id="w1"))
    await repo.upsert(WorkerStateRecord(worker_id="w2"))

    deleted = await repo.delete("w1")
    assert deleted is True

    fetched = await repo.get("w1")
    assert fetched is None

    remaining = await repo.list_all()
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_worker_state_get_nonexistent(pool):
    repo = WorkerStateRepo(pool)
    fetched = await repo.get("nonexistent")
    assert fetched is None


@pytest.mark.asyncio
async def test_event_log_insert_and_list(pool):
    repo = EventLogRepo(pool)
    rec = EventLogRecord(
        event_uuid="uuid-1",
        event_type="TEST_EVENT",
        source="test",
        payload={"key": "value"},
        priority="HIGH",
        status="PROCESSED",
    )
    await repo.insert(rec)

    events = await repo.list_recent()
    assert len(events) == 1
    assert events[0].event_uuid == "uuid-1"
    assert events[0].payload == {"key": "value"}


@pytest.mark.asyncio
async def test_event_log_multiple(pool):
    repo = EventLogRepo(pool)
    for i in range(5):
        await repo.insert(
            EventLogRecord(
                event_uuid=f"uuid-{i}",
                event_type="EVENT",
                source="test",
            )
        )

    events = await repo.list_recent(limit=3)
    assert len(events) == 3


@pytest.mark.asyncio
async def test_budget_snapshot_insert_and_list(pool):
    repo = BudgetSnapshotRepo(pool)
    rec = BudgetSnapshotRecord(
        worker_id="w1",
        total_requests=1000,
        total_failures=1,
        error_rate=0.001,
        budget_consumed=0.0005,
        status="NOMINAL",
    )
    await repo.insert(rec)

    snapshots = await repo.list_recent(worker_id="w1")
    assert len(snapshots) == 1
    assert snapshots[0].total_requests == 1000


@pytest.mark.asyncio
async def test_scorpion_finding_insert_and_list(pool):
    repo = ScorpionFindingRepo(pool)
    rec = ScorpionFindingRecord(
        scan_id="scan-001",
        worker_id="w1",
        vector_id="SC-03",
        severity="CRITICAL",
        description="Watchdog neutralization attempt",
        mitigated=False,
    )
    await repo.insert(rec)

    findings = await repo.list_unmitigated()
    assert len(findings) >= 1
    assert findings[0].vector_id == "SC-03"
