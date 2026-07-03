from app.vibe_diff.dashboard import ReviewDecision, VibeDiffDashboard, VibeDiffRecord


class TestVibeDiffRecord:
    def test_to_dict_keys(self):
        record = VibeDiffRecord(
            worker_id="test_worker",
            action_type="test_action",
            action_payload={"key": "value"},
            confidence=0.5,
        )
        d = record.to_dict()
        assert "decision_id" in d
        assert "worker_id" in d
        assert d["worker_id"] == "test_worker"
        assert d["confidence"] == 0.5
        assert d["status"] == "pending"

    def test_default_status_pending(self):
        record = VibeDiffRecord()
        assert record.status == ReviewDecision.PENDING


class TestVibeDiffDashboard:
    def test_initial_state(self):
        d = VibeDiffDashboard()
        assert d.pending_count() == 0
        stats = d.get_stats()
        assert stats["pending"] == 0
        assert stats["decided"] == 0

    def test_submit_high_confidence_returns_none(self):
        d = VibeDiffDashboard(confidence_threshold=0.7)
        result = d.submit_decision(
            worker_id="w1",
            action_type="test",
            action_payload={"k": "v"},
            confidence=0.95,
        )
        assert result is None
        assert d.pending_count() == 0

    def test_submit_low_confidence_creates_record(self):
        d = VibeDiffDashboard(confidence_threshold=0.7)
        result = d.submit_decision(
            worker_id="w1",
            action_type="test",
            action_payload={"k": "v"},
            confidence=0.4,
        )
        assert result is not None
        assert result.worker_id == "w1"
        assert result.action_type == "test"
        assert result.status == ReviewDecision.PENDING
        assert d.pending_count() == 1

    def test_submit_with_custom_threshold(self):
        d = VibeDiffDashboard(confidence_threshold=0.9)
        result = d.submit_decision("w1", "t", {"k": "v"}, confidence=0.85)
        assert result is not None

    def test_review_decision_approve(self):
        d = VibeDiffDashboard()
        record = d.submit_decision("w1", "t", {"k": "v"}, confidence=0.3)
        assert record is not None
        success = d.review_decision(
            record.decision_id, ReviewDecision.APPROVED, reviewer="admin"
        )
        assert success
        assert d.pending_count() == 0
        stats = d.get_stats()
        assert stats["approved"] == 1

    def test_review_decision_reject(self):
        d = VibeDiffDashboard()
        record = d.submit_decision("w1", "t", {"k": "v"}, confidence=0.3)
        assert record is not None
        success = d.review_decision(
            record.decision_id, ReviewDecision.REJECTED, reviewer="auditor"
        )
        assert success
        stats = d.get_stats()
        assert stats["rejected"] == 1

    def test_review_decision_escalate(self):
        d = VibeDiffDashboard()
        record = d.submit_decision("w1", "t", {"k": "v"}, confidence=0.3)
        assert record is not None
        success = d.review_decision(
            record.decision_id, ReviewDecision.ESCALATED, reviewer="manager"
        )
        assert success
        stats = d.get_stats()
        assert stats["escalated"] == 1

    def test_review_nonexistent_decision(self):
        d = VibeDiffDashboard()
        success = d.review_decision("nonexistent-id", ReviewDecision.APPROVED)
        assert not success

    def test_get_pending_filter_by_worker(self):
        d = VibeDiffDashboard()
        d.submit_decision("w1", "a", {}, 0.3)
        d.submit_decision("w2", "b", {}, 0.4)
        d.submit_decision("w1", "c", {}, 0.5)
        pending_w1 = d.get_pending(worker_id="w1")
        assert len(pending_w1) == 2
        pending_w2 = d.get_pending(worker_id="w2")
        assert len(pending_w2) == 1

    def test_get_pending_filter_by_action(self):
        d = VibeDiffDashboard()
        d.submit_decision("w1", "read", {}, 0.3)
        d.submit_decision("w1", "write", {}, 0.4)
        d.submit_decision("w1", "read", {}, 0.5)
        pending_read = d.get_pending(action_type="read")
        assert len(pending_read) == 2

    def test_get_decided_respects_limit(self):
        d = VibeDiffDashboard()
        r1 = d.submit_decision("w1", "t", {}, 0.3)
        r2 = d.submit_decision("w1", "t", {}, 0.4)
        r3 = d.submit_decision("w1", "t", {}, 0.5)
        assert r1 and r2 and r3
        d.review_decision(r1.decision_id, ReviewDecision.APPROVED)
        d.review_decision(r2.decision_id, ReviewDecision.REJECTED)
        d.review_decision(r3.decision_id, ReviewDecision.APPROVED)
        decided = d.get_decided(limit=2)
        assert len(decided) == 2

    def test_max_pending_limit(self):
        d = VibeDiffDashboard(confidence_threshold=1.0, max_pending=3)
        d.submit_decision("w1", "a", {}, 0.1)
        d.submit_decision("w1", "b", {}, 0.1)
        d.submit_decision("w1", "c", {}, 0.1)
        result = d.submit_decision("w1", "d", {}, 0.1)
        assert result is None
        assert d.pending_count() == 3

    def test_callback_fires_on_submit(self):
        records = []
        d = VibeDiffDashboard(on_review_callback=lambda r: records.append(r))
        d.submit_decision("w1", "t", {}, 0.3)
        assert len(records) == 1
        assert records[0].worker_id == "w1"

    def test_get_stats_all_zeros_initially(self):
        d = VibeDiffDashboard()
        stats = d.get_stats()
        assert stats == {
            "pending": 0,
            "decided": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "threshold": 0.7,
            "max_pending": 1000,
        }

    def test_auto_reject_expired(self):
        d = VibeDiffDashboard()
        d.submit_decision("w1", "t", {}, 0.3)
        expired = d.auto_reject_expired(max_age_seconds=-1)
        assert expired == 1
        assert d.pending_count() == 0
        stats = d.get_stats()
        assert stats["rejected"] == 1

    def test_auto_reject_young_records(self):
        d = VibeDiffDashboard()
        d.submit_decision("w1", "t", {}, 0.3)
        expired = d.auto_reject_expired(max_age_seconds=86400)
        assert expired == 0
        assert d.pending_count() == 1
