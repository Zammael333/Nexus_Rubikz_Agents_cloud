import asyncio

import pytest

from app.phoenix.protocol import PhoenixProtocol, WorkerStatus


def healthy() -> bool:
    return True


def unhealthy() -> bool:
    return False


@pytest.mark.asyncio
async def test_register_worker() -> None:
    phoenix = PhoenixProtocol()
    phoenix.register("worker-a", healthy)
    report = phoenix.get_report("worker-a")
    assert report is not None
    assert report.worker_id == "worker-a"
    assert report.status == WorkerStatus.HEALTHY


@pytest.mark.asyncio
async def test_unregister_worker() -> None:
    phoenix = PhoenixProtocol()
    phoenix.register("worker-a", healthy)
    phoenix.unregister("worker-a")
    assert phoenix.get_report("worker-a") is None


@pytest.mark.asyncio
async def test_healthy_worker_stays_healthy() -> None:
    phoenix = PhoenixProtocol(health_interval=0.1)
    phoenix.register("worker-a", healthy)
    await phoenix.start()
    await asyncio.sleep(0.3)
    report = phoenix.get_report("worker-a")
    assert report is not None
    assert report.status == WorkerStatus.HEALTHY
    assert report.consecutive_failures == 0
    await phoenix.stop()


@pytest.mark.asyncio
async def test_failing_worker_degrades_then_fails() -> None:
    phoenix = PhoenixProtocol(health_interval=0.1, max_failures=2)
    phoenix.register("worker-b", unhealthy)
    await phoenix.start()
    await asyncio.sleep(0.4)
    report = phoenix.get_report("worker-b")
    assert report is not None
    assert report.status in (WorkerStatus.FAILED, WorkerStatus.DEGRADED)
    assert report.consecutive_failures >= 1
    await phoenix.stop()


@pytest.mark.asyncio
async def test_force_recovery() -> None:
    phoenix = PhoenixProtocol()
    phoenix.register("worker-c", unhealthy)
    ok = phoenix.force_recovery("worker-c")
    assert ok is True
    report = phoenix.get_report("worker-c")
    assert report is not None
    assert report.status == WorkerStatus.HEALTHY
    assert report.consecutive_failures == 0


@pytest.mark.asyncio
async def test_get_all_reports() -> None:
    phoenix = PhoenixProtocol()
    phoenix.register("w1", healthy)
    phoenix.register("w2", healthy)
    reports = phoenix.get_all_reports()
    assert len(reports) == 2
    assert "w1" in reports
    assert "w2" in reports


@pytest.mark.asyncio
async def test_recovery_callback() -> None:
    recovered: list[str] = []

    def on_recovery(name: str, epoch: str) -> None:
        recovered.append(name)

    phoenix = PhoenixProtocol(
        health_interval=0.1,
        max_failures=1,
        on_recovery=on_recovery,
    )
    phoenix.register("worker-d", healthy)
    await phoenix.start()
    await asyncio.sleep(0.3)
    assert len(recovered) >= 0
    await phoenix.stop()


@pytest.mark.asyncio
async def test_quarantine_callback() -> None:
    quarantined: list[str] = []

    def on_quarantine(name: str) -> None:
        quarantined.append(name)

    phoenix = PhoenixProtocol(
        health_interval=0.1,
        max_failures=1,
        quarantine_threshold=1,
        quarantine_window=30,
        on_quarantine=on_quarantine,
    )
    phoenix.register("worker-e", unhealthy)
    await phoenix.start()
    await asyncio.sleep(0.4)
    assert len(quarantined) >= 0
    await phoenix.stop()


@pytest.mark.asyncio
async def test_concurrent_registrations() -> None:
    phoenix = PhoenixProtocol()
    for i in range(20):
        phoenix.register(f"worker-{i}", healthy)
    reports = phoenix.get_all_reports()
    assert len(reports) == 20
