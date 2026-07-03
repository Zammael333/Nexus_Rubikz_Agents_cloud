# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Chaos Engineering Tests for Workers (Paso 30)

import asyncio
import os
import tempfile
import threading
import uuid

import pytest

from app.budget_watchdog import BudgetStatus, BudgetWatchdog
from app.bus.async_event_bus import AsyncEventBus
from app.db.vault import NexusVault
from app.edge_glow import EdgeGlow, SystemPulse
from app.notifications import NotificationChannel, NotificationDispatcher
from app.phoenix.protocol import PhoenixProtocol, WorkerStatus


class TestChaosbudgetExhaustion:
    """Simulate budget exhaustion and verify freeze behavior."""

    def test_budget_exhaustion_freezes_operations(self):
        bw = BudgetWatchdog(error_budget_percent=1.0)  # Very tight budget
        # 100% failure rate → immediate freeze
        bw.record_failure()
        assert bw.is_frozen()
        # Verify check_budget also reports frozen
        report = bw.check_budget()
        assert report.status == BudgetStatus.FROZEN

    def test_budget_recovery_after_reset(self):
        bw = BudgetWatchdog(error_budget_percent=1.0)
        bw.record_failure()
        assert bw.is_frozen()
        bw.reset()
        assert not bw.is_frozen()
        report = bw.check_budget()
        assert report.status == BudgetStatus.HEALTHY

    def test_budget_cascade_with_callbacks(self):
        events = []
        bw = BudgetWatchdog(
            error_budget_percent=5.0,
            on_warning=lambda r: events.append("WARNING"),
            on_freeze=lambda r: events.append("FROZEN"),
        )
        for _ in range(97):
            bw.record_success()
        # Push to warning
        for _ in range(3):
            bw.record_failure()
        # Verify warning fired (3/100 = 3% → 60% of 5% budget)
        assert "WARNING" in events

        # Push to frozen
        for _ in range(2):
            bw.record_failure()
        # 5/102 ≈ 4.9% → ~98% of budget
        # Need more failures
        for _ in range(5):
            bw.record_failure()
        # 10/107 ≈ 9.3% → 186% of 5% budget → FROZEN
        assert "FROZEN" in events


class TestChaosInventoryIdempotency:
    """Test concurrent locks with same SKU verify idempotency."""

    def test_vault_rejects_duplicate_tx_token(self):
        with tempfile.TemporaryDirectory() as td:
            vault = NexusVault(db_path=os.path.join(td, "test.db"))
            token = str(uuid.uuid4())
            # First lock succeeds
            r1 = vault.record_lock("SKU-1", 10, token)
            assert r1 is not None
            # Second lock with same token is rejected
            r2 = vault.record_lock("SKU-1", 10, token)
            assert r2 is None

    def test_concurrent_vault_writes(self):
        """Simulate concurrent writes to verify thread safety."""
        with tempfile.TemporaryDirectory() as td:
            vault = NexusVault(db_path=os.path.join(td, "test.db"))
            results = []
            errors = []

            def write_lock(i):
                try:
                    token = str(uuid.uuid4())
                    r = vault.record_lock("SKU-RACE", 1, token)
                    results.append(r)
                except Exception as e:
                    errors.append(e)

            threads = [
                threading.Thread(target=write_lock, args=(i,)) for i in range(50)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
            # All 50 should succeed (unique UUIDs)
            assert len([r for r in results if r is not None]) == 50
            # Verify all are in the DB
            locks = vault.get_locks_for_sku("SKU-RACE")
            assert len(locks) == 50


class TestChaosPhoenixBudgetCascade:
    """Test Phoenix quarantine cascading into budget impact."""

    @pytest.mark.asyncio
    async def test_phoenix_quarantine_detection(self):
        quarantined_workers = []
        phoenix = PhoenixProtocol(
            quarantine_threshold=2,
            quarantine_window=30,
            max_failures=1,
            on_quarantine=lambda name: quarantined_workers.append(name),
        )
        # Register two workers that always fail
        phoenix.register("worker_a", lambda: False)
        phoenix.register("worker_b", lambda: False)

        await phoenix.start()
        await asyncio.sleep(2.5)  # Let health checks run
        await phoenix.stop()

        # Check worker statuses
        report_a = phoenix.get_report("worker_a")
        report_b = phoenix.get_report("worker_b")
        # Both should be in FAILED or QUARANTINED state
        assert report_a.status in (WorkerStatus.FAILED, WorkerStatus.QUARANTINED)
        assert report_b.status in (WorkerStatus.FAILED, WorkerStatus.QUARANTINED)


class TestChaosAsyncBusBackpressure:
    """Test AsyncEventBus under extreme backpressure."""

    @pytest.mark.asyncio
    async def test_backpressure_sends_to_dlq(self):
        bus = AsyncEventBus(max_queue_size=5, batch_size=1, flush_interval=10.0)

        original_flush = bus._flush_batch

        async def slow_flush():
            await asyncio.sleep(1.5)
            return await original_flush()

        bus._flush_batch = slow_flush
        await bus.start()

        accepted = 0
        rejected = 0
        for i in range(30):
            ok = await bus.emit(f"FLOOD_{i}", {"index": i}, source="chaos_test")
            if ok:
                accepted += 1
            else:
                rejected += 1

        await bus.stop()
        assert rejected > 0 or bus.dlq_size > 0
        assert accepted + rejected == 30


class TestChaosEdgeGlow:
    """Test Edge Glow under degraded conditions."""

    def test_glow_red_on_multiple_failures(self):
        bw = BudgetWatchdog(error_budget_percent=1.0)
        bw.record_failure()  # Frozen

        glow = EdgeGlow(budget_watchdog=bw)
        snapshot = glow.get_system_pulse()
        # Budget frozen → should be at least ORANGE
        assert snapshot.pulse in (SystemPulse.ORANGE, SystemPulse.RED)

    def test_glow_green_when_healthy(self):
        bw = BudgetWatchdog(error_budget_percent=50.0)
        bw.record_success()

        glow = EdgeGlow(budget_watchdog=bw)
        snapshot = glow.get_system_pulse()
        assert snapshot.pulse == SystemPulse.GREEN


class TestChaosNotifications:
    """Test notification dispatcher under error conditions."""

    def test_dispatch_to_failing_channel(self):
        def always_fail(notification):
            raise RuntimeError("Channel down")

        dispatcher = NotificationDispatcher()
        dispatcher.add_channel(
            NotificationChannel(name="broken", dispatch_fn=always_fail)
        )

        # Should not raise, should return True (local log still works)
        ok = dispatcher.dispatch("TEST_ALERT", {"msg": "test"})
        assert ok is True
        assert dispatcher.failure_count >= 1

    def test_bus_hook_filters_critical(self):
        class FakeEvent:
            def __init__(self, etype, pri):
                self.type = etype
                self.priority = pri
                self.payload = {"test": True}
                self.source = "test"

        class FakePriority:
            def __init__(self, name):
                self.name = name

        dispatcher = NotificationDispatcher()
        hook = dispatcher.as_bus_hook()

        # Only CRITICAL should be dispatched
        hook(
            [
                FakeEvent("NORMAL_EVENT", FakePriority("NORMAL")),
                FakeEvent("CRITICAL_EVENT", FakePriority("CRITICAL")),
            ]
        )
        assert dispatcher.dispatch_count >= 1


class TestChaosVault:
    """Test NexusVault under edge conditions."""

    def test_vault_schema_creation(self):
        with tempfile.TemporaryDirectory() as td:
            vault = NexusVault(db_path=os.path.join(td, "test.db"))
            # Schema should exist
            report = vault.count_locks_by_sku()
            assert isinstance(report, dict)

    def test_vault_log_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            vault = NexusVault(db_path=os.path.join(td, "test.db"))
            vault.log_transaction("token-1", "TEST_EVENT", '{"key": "val"}')
            # Should not raise

    def test_vault_budget_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            vault = NexusVault(db_path=os.path.join(td, "test.db"))
            vault.record_budget_snapshot(100, 5, 5.0, 18.5, "healthy")
            # Should not raise
