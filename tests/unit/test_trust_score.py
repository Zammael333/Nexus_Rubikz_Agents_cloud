from app.trust_score.scorer import ScoreFactor, ScoreReport, TrustScorer


class TestScoreReport:
    def test_to_dict(self):
        report = ScoreReport(
            worker_id="w1",
            overall_score=0.85,
            factors={"consecutive_failures": 0.9},
            breakdown={"consecutive_failures": 0.9},
        )
        d = report.to_dict()
        assert d["worker_id"] == "w1"
        assert d["overall_score"] == 0.85
        assert d["factors"]["consecutive_failures"] == 0.9


class TestTrustScorer:
    def test_initial_state(self):
        ts = TrustScorer()
        assert ts.get_latest("any") is None

    def test_perfect_score(self):
        ts = TrustScorer()
        report = ts.compute("w1")
        assert report.overall_score >= 0.95
        assert ts.interpret(report.overall_score) == "TRUSTED"

    def test_low_trust_from_failures(self):
        ts = TrustScorer()
        report = ts.compute(
            "w1",
            consecutive_failures=10,
            neutralization_attempts=3,
            budget_consumed=1.0,
            watchdog_violations=5,
        )
        assert report.overall_score < 0.5
        assert ts.interpret(report.overall_score) in ("SUSPICIOUS", "CONTAIN")

    def test_monitor_range(self):
        ts = TrustScorer()
        report = ts.compute(
            "w1",
            consecutive_failures=3,
            watchdog_violations=2,
            budget_consumed=0.3,
        )
        score = report.overall_score
        if 0.70 <= score < 0.85:
            assert ts.interpret(score) == "MONITOR"
        elif score >= 0.85:
            assert ts.interpret(score) in ("RELIABLE", "TRUSTED")

    def test_consecutive_failures_impact(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", consecutive_failures=0)
        r5 = ts.compute("w1", consecutive_failures=5)
        assert r5.overall_score < r0.overall_score

    def test_neutralization_attempts_impact(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", neutralization_attempts=0)
        r3 = ts.compute("w1", neutralization_attempts=3)
        assert r3.overall_score < r0.overall_score

    def test_budget_consumption_impact(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", budget_consumed=0.0)
        r1 = ts.compute("w1", budget_consumed=1.0)
        assert r1.overall_score < r0.overall_score

    def test_uptime_benefit(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", uptime_hours=0)
        r720 = ts.compute("w1", uptime_hours=720)
        assert r720.overall_score >= r0.overall_score

    def test_get_history(self):
        ts = TrustScorer()
        ts.compute("w1", consecutive_failures=0)
        ts.compute("w1", consecutive_failures=1)
        ts.compute("w1", consecutive_failures=2)
        history = ts.get_history("w1")
        assert len(history) == 3
        assert history[0].factors.get("consecutive_failures", 0) >= 0
        assert history[-1].factors.get("consecutive_failures", 0) < history[
            0
        ].factors.get("consecutive_failures", 1)

    def test_get_history_limit(self):
        ts = TrustScorer()
        for i in range(20):
            ts.compute("w1", consecutive_failures=i)
        history = ts.get_history("w1", limit=5)
        assert len(history) == 5

    def test_get_latest(self):
        ts = TrustScorer()
        ts.compute("w1", consecutive_failures=0)
        ts.compute("w1", consecutive_failures=5)
        latest = ts.get_latest("w1")
        assert latest is not None
        assert latest.factors.get("consecutive_failures", 1) < 1.0

    def test_get_latest_none(self):
        ts = TrustScorer()
        assert ts.get_latest("nonexistent") is None

    def test_interpret_all_levels(self):
        ts = TrustScorer()
        assert ts.interpret(0.96) == "TRUSTED"
        assert ts.interpret(0.90) == "RELIABLE"
        assert ts.interpret(0.75) == "MONITOR"
        assert ts.interpret(0.60) == "SUSPICIOUS"
        assert ts.interpret(0.40) == "CONTAIN"

    def test_set_weight(self):
        ts = TrustScorer()
        ts.set_weight(ScoreFactor.CONSECUTIVE_FAILURES, 0.5)
        assert ts._weights[ScoreFactor.CONSECUTIVE_FAILURES] == 0.5

    def test_set_weight_clamps(self):
        ts = TrustScorer()
        ts.set_weight(ScoreFactor.CONSECUTIVE_FAILURES, 2.0)
        assert ts._weights[ScoreFactor.CONSECUTIVE_FAILURES] == 1.0
        ts.set_weight(ScoreFactor.CONSECUTIVE_FAILURES, -0.5)
        assert ts._weights[ScoreFactor.CONSECUTIVE_FAILURES] == 0.0

    def test_normalize_weights(self):
        ts = TrustScorer()
        ts.set_weight(ScoreFactor.CONSECUTIVE_FAILURES, 1.0)
        ts.set_weight(ScoreFactor.UPTIME, 0.0)
        ts.normalize_weights()
        total = sum(ts._weights.values())
        assert abs(total - 1.0) < 1e-6

    def test_history_capped_at_100(self):
        ts = TrustScorer()
        for i in range(150):
            ts.compute("w1", consecutive_failures=i)
        assert len(ts._score_history["w1"]) == 100

    def test_quarantine_history_impact(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", quarantine_count=0)
        r5 = ts.compute("w1", quarantine_count=5)
        assert r5.overall_score <= r0.overall_score

    def test_scorpion_findings_impact(self):
        ts = TrustScorer()
        r0 = ts.compute("w1", scorpion_findings=0)
        r10 = ts.compute("w1", scorpion_findings=10)
        assert r10.overall_score <= r0.overall_score
