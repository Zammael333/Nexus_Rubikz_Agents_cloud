import asyncio
import os
import tempfile

import pytest
import pytest_asyncio

from app.db.connection import AsyncDbPool, CloudSqlConfig
from app.db.migrations import ensure_schema
from app.db.repository import WorkerStateRepo
from app.phoenix.protocol import PhoenixProtocol, WorkerStatus


def healthy() -> bool:
    return True


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


@pytest_asyncio.fixture
async def repo(pool):
    return WorkerStateRepo(pool)


@pytest.mark.asyncio
async def test_phoenix_persists_after_register(repo):
    phoenix = PhoenixProtocol(repo=repo)
    phoenix.register("worker-persist-1", healthy)

    health = phoenix.get_report("worker-persist-1")
    assert health is not None

    phoenix.force_recovery("worker-persist-1")
    await asyncio.sleep(0.05)

    fetched = await repo.get("worker-persist-1")
    assert fetched is not None
    assert fetched.worker_id == "worker-persist-1"
    assert fetched.status == "healthy"


@pytest.mark.asyncio
async def test_phoenix_health_loop_persists_state(repo):
    phoenix = PhoenixProtocol(repo=repo, health_interval=0.1)
    phoenix.register("health-loop", healthy)
    await phoenix.start()

    await asyncio.sleep(0.35)
    await phoenix.stop()

    fetched = await repo.get("health-loop")
    assert fetched is not None
    assert fetched.status == "healthy"
    assert fetched.last_heartbeat != ""


@pytest.mark.asyncio
async def test_phoenix_persists_force_recovery(repo):
    phoenix = PhoenixProtocol(repo=repo)
    phoenix.register("worker-recover", healthy)
    phoenix.force_recovery("worker-recover")
    await asyncio.sleep(0.05)

    fetched = await repo.get("worker-recover")
    assert fetched is not None
    assert fetched.status == "healthy"


@pytest.mark.asyncio
async def test_phoenix_no_repo_still_works():
    phoenix = PhoenixProtocol(repo=None)
    phoenix.register("no-repo", healthy)
    report = phoenix.get_report("no-repo")
    assert report is not None
    assert report.status == WorkerStatus.HEALTHY
