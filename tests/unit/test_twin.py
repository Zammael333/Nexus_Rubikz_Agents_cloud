from __future__ import annotations

import asyncio

import pytest

from app.twin.emitter import DigitalTwinEmitter, TwinSnapshot

pytestmark = pytest.mark.asyncio(scope="function")


class TestTwinSnapshot:
    def test_defaults(self):
        s = TwinSnapshot(worker_id="w1", status="ok", state={"cpu": 0.5})
        assert s.worker_id == "w1"
        assert s.status == "ok"
        assert s.state == {"cpu": 0.5}
        assert s.trust_score is None
        assert isinstance(s.timestamp, str)

    def test_to_dict(self):
        s = TwinSnapshot(
            worker_id="w1",
            status="ok",
            state={"cpu": 0.5},
            trust_score=0.9,
            spiffe_id="spiffe://test/w1",
        )
        d = s.to_dict()
        assert d["worker_id"] == "w1"
        assert d["trust_score"] == 0.9
        assert d["spiffe_id"] == "spiffe://test/w1"
        assert "timestamp" in d

    def test_to_dict_no_optional(self):
        s = TwinSnapshot(worker_id="w2", status="error", state={"error": "fail"})
        d = s.to_dict()
        assert d["trust_score"] is None
        assert d["spiffe_id"] == ""


class TestDigitalTwinEmitter:
    async def test_init_defaults(self):
        e = DigitalTwinEmitter()
        assert e._poll_interval == 5.0
        assert e._running is False
        assert e.mirror_size == 0

    async def test_init_custom_interval(self):
        e = DigitalTwinEmitter(poll_interval=1.0)
        assert e._poll_interval == 1.0

    async def test_register_provider(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {"cpu": 0.5}})
        assert "w1" in e._providers

    async def test_unregister_provider(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        e.unregister_provider("w1")
        assert "w1" not in e._providers
        assert "w1" not in e._mirror

    async def test_poll_once_sync(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {"cpu": 0.5}})
        snapshots = await e.poll_once()
        assert len(snapshots) == 1
        assert snapshots[0].worker_id == "w1"
        assert snapshots[0].state == {"cpu": 0.5}

    async def test_poll_once_async(self):
        e = DigitalTwinEmitter()

        async def provider():
            return {"status": "ok", "data": {"mem": 0.8}}

        e.register_provider("a1", provider)
        snapshots = await e.poll_once()
        assert len(snapshots) == 1
        assert snapshots[0].state == {"mem": 0.8}

    async def test_poll_once_with_trust(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "w1",
            lambda: {
                "status": "ok",
                "data": {},
                "trust_score": 0.95,
                "spiffe_id": "spiffe://test/w1",
            },
        )
        snapshots = await e.poll_once()
        assert snapshots[0].trust_score == 0.95
        assert snapshots[0].spiffe_id == "spiffe://test/w1"

    async def test_poll_once_error(self):
        e = DigitalTwinEmitter()

        def broken():
            msg = "fail"
            raise ValueError(msg)

        e.register_provider("w1", broken)
        snapshots = await e.poll_once()
        assert snapshots[0].status == "error"
        assert "fail" in snapshots[0].state["error"]

    async def test_get_snapshot(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        await e.poll_once()
        snap = e.get_snapshot("w1")
        assert snap is not None
        assert snap.worker_id == "w1"

    async def test_get_snapshot_not_found(self):
        e = DigitalTwinEmitter()
        assert e.get_snapshot("ghost") is None

    async def test_get_all_snapshots(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {"a": 1}})
        e.register_provider("w2", lambda: {"status": "ok", "data": {"b": 2}})
        await e.poll_once()
        all_snaps = e.get_all_snapshots()
        assert len(all_snaps) == 2

    async def test_mirror_size(self):
        e = DigitalTwinEmitter()
        assert e.mirror_size == 0
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        await e.poll_once()
        assert e.mirror_size == 1

    async def test_get_drift(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "w1", lambda: {"status": "ok", "data": {}, "trust_score": 0.95}
        )
        await e.poll_once()
        drift = e.get_drift("w1")
        assert drift == pytest.approx(0.05, abs=1e-9)

    async def test_get_drift_no_trust(self):
        e = DigitalTwinEmitter()
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        await e.poll_once()
        assert e.get_drift("w1") == 1.0

    async def test_get_drift_missing_worker(self):
        e = DigitalTwinEmitter()
        assert e.get_drift("ghost") == 1.0

    async def test_count_drifted(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "w1", lambda: {"status": "ok", "data": {}, "trust_score": 1.0}
        )
        e.register_provider(
            "w2", lambda: {"status": "ok", "data": {}, "trust_score": 0.8}
        )
        await e.poll_once()
        assert e.count_drifted(threshold=0.5) == 0
        assert e.count_drifted(threshold=0.1) == 1

    async def test_register_callback(self):
        e = DigitalTwinEmitter()
        calls: list[str] = []

        def cb(snapshot):
            calls.append(snapshot.worker_id)

        e.register_callback(cb)
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        await e.poll_once()
        assert "w1" in calls

    async def test_start_stop(self):
        e = DigitalTwinEmitter(poll_interval=0.1)
        e.register_provider("w1", lambda: {"status": "ok", "data": {}})
        await e.start()
        assert e._running is True
        await asyncio.sleep(0.15)
        assert e.mirror_size == 1
        await e.stop()
        assert e._running is False

    async def test_double_start_noop(self):
        e = DigitalTwinEmitter(poll_interval=0.5)
        await e.start()
        await e.start()
        assert e._running is True
        await e.stop()

    async def test_to_dict(self):
        e = DigitalTwinEmitter(poll_interval=2.0)
        e.register_provider("w1", lambda: {"status": "ok", "data": {"cpu": 0.5}})
        await e.poll_once()
        d = e.to_dict()
        assert d["poll_interval"] == 2.0
        assert d["running"] is False
        assert "w1" in d["mirror"]
