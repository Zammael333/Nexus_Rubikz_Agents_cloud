from __future__ import annotations

from app.killswitch.detector import RecursionDetector, RecursionRecord


class TestRecursionRecord:
    def test_defaults(self):
        r = RecursionRecord(
            source_worker="w1",
            target_worker="w2",
            action="execute",
            count=1,
            first_seen="ts1",
            last_seen="ts1",
        )
        assert r.cutoff is False

    def test_to_dict(self):
        r = RecursionRecord(
            source_worker="w1",
            target_worker="w2",
            action="execute",
            count=3,
            first_seen="ts1",
            last_seen="ts2",
            cutoff=True,
        )
        d = r.to_dict()
        assert d["source_worker"] == "w1"
        assert d["target_worker"] == "w2"
        assert d["count"] == 3
        assert d["cutoff"] is True


class TestRecursionDetector:
    def test_init_defaults(self):
        d = RecursionDetector()
        assert d.max_depth == 5
        assert d.max_count == 10
        assert d._window_seconds == 60.0

    def test_init_custom(self):
        d = RecursionDetector(max_depth=3, max_count=5, window_seconds=30.0)
        assert d.max_depth == 3
        assert d.max_count == 5
        assert d._window_seconds == 30.0

    def test_record_invocation_first_call(self):
        d = RecursionDetector()
        r = d.record_invocation(target="w2", action="execute", source="w1")
        assert r.source_worker == "w1"
        assert r.target_worker == "w2"
        assert r.count == 1
        assert r.cutoff is False

    def test_record_invocation_increments(self):
        d = RecursionDetector()
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        r = d.record_invocation(target="w2", action="execute", source="w1")
        assert r.count == 3

    def test_record_invocation_without_source(self):
        d = RecursionDetector()
        r = d.record_invocation(target="w2", action="execute")
        assert r.source_worker == ""
        assert r.target_worker == "w2"

    def test_cutoff_by_max_count(self):
        d = RecursionDetector(max_count=3)
        for _ in range(3):
            d.record_invocation(target="w2", action="execute", source="w1")
        assert d.is_cutoff(target="w2", action="execute", source="w1") is True

    def test_not_cutoff_below_threshold(self):
        d = RecursionDetector(max_count=5)
        for _ in range(4):
            d.record_invocation(target="w2", action="execute", source="w1")
        assert d.is_cutoff(target="w2", action="execute", source="w1") is False

    def test_cutoff_different_key_isolated(self):
        d = RecursionDetector(max_count=2)
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        assert d.is_cutoff(target="w2", action="execute", source="w1") is True
        assert d.is_cutoff(target="w3", action="execute", source="w1") is False

    def test_reset_cutoff(self):
        d = RecursionDetector(max_count=2)
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        assert d.is_cutoff(target="w2", action="execute", source="w1") is True
        d.reset_cutoff(target="w2", action="execute", source="w1")
        assert d.is_cutoff(target="w2", action="execute", source="w1") is False

    def test_reset_all(self):
        d = RecursionDetector(max_count=2)
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        d.reset_all()
        assert len(d._invocations) == 0
        assert len(d._cutoff) == 0
        assert len(d._records) == 0

    def test_active_cutoffs(self):
        d = RecursionDetector(max_count=2)
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        assert len(d.active_cutoffs) == 1

    def test_all_records(self):
        d = RecursionDetector()
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w3", action="deploy", source="w2")
        assert len(d.all_records) == 2

    def test_no_active_cutoffs(self):
        d = RecursionDetector(max_count=10)
        d.record_invocation(target="w2", action="execute", source="w1")
        assert len(d.active_cutoffs) == 0

    def test_prune_expired(self):
        d = RecursionDetector(window_seconds=0.0, max_count=1)
        d.record_invocation(target="w2", action="execute", source="w1")
        import time

        time.sleep(0.01)
        r = d.record_invocation(target="w2", action="execute", source="w1")
        assert r.count == 1

    def test_to_dict(self):
        d = RecursionDetector(max_count=2)
        d.record_invocation(target="w2", action="execute", source="w1")
        d.record_invocation(target="w2", action="execute", source="w1")
        dd = d.to_dict()
        assert dd["max_depth"] == 5
        assert dd["max_count"] == 2
        assert dd["active_cutoffs"] == 1
