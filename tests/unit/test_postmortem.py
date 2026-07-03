from __future__ import annotations

import pytest

from app.postmortem.store import (
    IncidentRecord,
    PostmortemStore,
    fingerprint_error,
)

pytestmark = pytest.mark.asyncio(scope="function")


class TestFingerprint:
    def test_consistent_hash(self):
        assert fingerprint_error("error x") == fingerprint_error("error x")

    def test_different_inputs(self):
        assert fingerprint_error("error a") != fingerprint_error("error b")

    def test_length(self):
        fp = fingerprint_error("some error message")
        assert len(fp) == 16

    def test_empty_string(self):
        fp = fingerprint_error("")
        assert len(fp) == 16


class TestIncidentRecord:
    def test_defaults(self):
        r = IncidentRecord(
            worker_id="w1",
            error_message="fail",
            error_fingerprint="abc123",
        )
        assert r.severity == "error"
        assert r.context == {}
        assert r.resolution == ""
        assert isinstance(r.incident_id, str)

    def test_to_dict(self):
        r = IncidentRecord(
            worker_id="w1",
            error_message="fail",
            error_fingerprint="abc123",
            severity="critical",
            context={"cpu": 0.9},
        )
        d = r.to_dict()
        assert d["worker_id"] == "w1"
        assert d["severity"] == "critical"
        assert d["context"] == {"cpu": 0.9}

    def test_from_dict(self):
        d = {
            "worker_id": "w1",
            "error_message": "timeout",
            "error_fingerprint": "def456",
            "severity": "warning",
            "context": {"mem": 0.95},
        }
        r = IncidentRecord.from_dict(d)
        assert r.worker_id == "w1"
        assert r.error_message == "timeout"
        assert r.severity == "warning"
        assert r.context == {"mem": 0.95}

    def test_from_dict_minimal(self):
        d = {
            "worker_id": "w2",
            "error_message": "err",
            "error_fingerprint": "xyz",
        }
        r = IncidentRecord.from_dict(d)
        assert r.severity == "error"
        assert r.resolution == ""


class TestPostmortemStore:
    async def test_init_defaults(self):
        store = PostmortemStore()
        await store.initialize()
        assert store.total_incidents == 0
        assert store._use_sqlite is False

    async def test_store_and_count(self):
        store = PostmortemStore()
        await store.initialize()
        rec = IncidentRecord(
            worker_id="w1",
            error_message="connection timeout",
            error_fingerprint=fingerprint_error("connection timeout"),
        )
        rid = await store.store(rec)
        assert rid == rec.incident_id
        assert store.total_incidents == 1

    async def test_store_multiple(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(worker_id="w1", error_message="e1", error_fingerprint="fp1")
        )
        await store.store(
            IncidentRecord(worker_id="w2", error_message="e2", error_fingerprint="fp2")
        )
        assert store.total_incidents == 2

    async def test_find_similar_by_fingerprint(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="timeout", error_fingerprint="fp_abc"
            )
        )
        await store.store(
            IncidentRecord(
                worker_id="w2", error_message="timeout", error_fingerprint="fp_abc"
            )
        )
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="other", error_fingerprint="fp_xyz"
            )
        )
        results = await store.find_similar("fp_abc")
        assert len(results) == 2

    async def test_find_similar_by_worker(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="timeout", error_fingerprint="fp_abc"
            )
        )
        await store.store(
            IncidentRecord(
                worker_id="w2", error_message="timeout", error_fingerprint="fp_abc"
            )
        )
        results = await store.find_similar("fp_abc", worker_id="w1")
        assert len(results) == 1
        assert results[0].worker_id == "w1"

    async def test_find_similar_no_match(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(worker_id="w1", error_message="x", error_fingerprint="fp1")
        )
        results = await store.find_similar("no_match")
        assert results == []

    async def test_find_by_worker(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(worker_id="w1", error_message="e1", error_fingerprint="fp1")
        )
        await store.store(
            IncidentRecord(worker_id="w1", error_message="e2", error_fingerprint="fp2")
        )
        await store.store(
            IncidentRecord(worker_id="w2", error_message="e3", error_fingerprint="fp3")
        )
        results = await store.find_by_worker("w1")
        assert len(results) == 2

    async def test_list_recent(self):
        store = PostmortemStore()
        await store.initialize()
        for i in range(5):
            await store.store(
                IncidentRecord(
                    worker_id="w1",
                    error_message=f"e{i}",
                    error_fingerprint=f"fp{i}",
                )
            )
        recent = await store.list_recent(limit=3)
        assert len(recent) == 3

    async def test_list_recent_default_limit(self):
        store = PostmortemStore()
        await store.initialize()
        for i in range(15):
            await store.store(
                IncidentRecord(
                    worker_id="w1",
                    error_message=f"e{i}",
                    error_fingerprint=f"fp{i}",
                )
            )
        recent = await store.list_recent()
        assert len(recent) == 10

    async def test_resolve(self):
        store = PostmortemStore()
        await store.initialize()
        rec = IncidentRecord(
            worker_id="w1", error_message="err", error_fingerprint="fp"
        )
        rid = await store.store(rec)
        ok = await store.resolve(rid, "fixed by restart")
        assert ok is True
        r = await store.find_similar("fp")
        assert r[0].resolution == "fixed by restart"
        assert r[0].resolved_at != ""

    async def test_resolve_not_found(self):
        store = PostmortemStore()
        await store.initialize()
        ok = await store.resolve("nonexistent", "nope")
        assert ok is False

    async def test_count_recurrences(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="boom", error_fingerprint="fp1"
            )
        )
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="boom", error_fingerprint="fp1"
            )
        )
        count = await store.count_recurrences("fp1")
        assert count == 2

    async def test_count_recurrences_no_match(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(
                worker_id="w1", error_message="boom", error_fingerprint="fp1"
            )
        )
        count = await store.count_recurrences("no_match")
        assert count == 0

    async def test_to_dict(self):
        store = PostmortemStore()
        await store.initialize()
        await store.store(
            IncidentRecord(worker_id="w1", error_message="err", error_fingerprint="fp1")
        )
        d = store.to_dict()
        assert d["total_incidents"] == 1
        assert d["use_sqlite"] is False
        assert len(d["recent"]) == 1

    async def test_close_noop_without_sqlite(self):
        store = PostmortemStore()
        await store.initialize()
        await store.close()
        assert store._conn is None
