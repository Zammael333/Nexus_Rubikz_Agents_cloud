from unittest.mock import MagicMock

from app.edge_glow import EdgeGlow, GlowSnapshot, SLOCalibrator, SystemPulse


class TestSLOCalibrator:
    def test_defaults(self):
        c = SLOCalibrator()
        assert c.nominal_slo == 0.999973
        assert c.error_budget == 0.000027
        assert len(c.history) == 0

    def test_calibrate_green(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999980, error_budget_remaining=1.0)
        assert r["slo_pulse"] == "green"
        assert r["gap"] < 0

    def test_calibrate_yellow(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999950, error_budget_remaining=0.7)
        assert r["slo_pulse"] == "yellow"

    def test_calibrate_orange(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999900, error_budget_remaining=0.4)
        assert r["slo_pulse"] == "orange"

    def test_calibrate_red(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999800, error_budget_remaining=0.2)
        assert r["slo_pulse"] == "red"

    def test_calibrate_red_high_usage(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999900, error_budget_remaining=0.01)
        assert r["slo_pulse"] == "red"

    def test_calibrate_green_when_above_slo(self):
        c = SLOCalibrator()
        r = c.calibrate(real_slo=0.999990, error_budget_remaining=0.95)
        assert r["slo_pulse"] == "green"
        assert r["gap"] < 0

    def test_history_grows(self):
        c = SLOCalibrator()
        for i in range(10):
            c.calibrate(real_slo=0.999973 - 0.000001 * i)
        assert len(c.history) == 10

    def test_history_capped(self):
        c = SLOCalibrator()
        for i in range(1100):
            c.calibrate(real_slo=0.999973 - 0.000001 * (i % 100))
        assert len(c.history) <= 600

    def test_get_history(self):
        c = SLOCalibrator()
        for _ in range(5):
            c.calibrate(real_slo=0.999973)
        h = c.get_history(limit=2)
        assert len(h) == 2

    def test_to_dict(self):
        c = SLOCalibrator()
        c.calibrate(real_slo=0.999980)
        d = c.to_dict()
        assert d["nominal_slo"] == 0.999973
        assert d["history_size"] == 1


class TestGlowSnapshot:
    def test_to_dict_includes_slo(self):
        s = GlowSnapshot(
            pulse=SystemPulse.GREEN,
            workers={"status": "NOMINAL"},
            budget={"status": "ok"},
            bus={"dlq_size": 0},
            scorpion_vectors={},
            slo={"slo_pulse": "green", "nominal_slo": 0.999973},
            timestamp="2026-01-01T00:00:00",
        )
        d = s.to_dict()
        assert d["pulse"] == "green"
        assert d["slo"]["slo_pulse"] == "green"


class TestEdgeGlowSystemPulse:
    def test_green_no_components(self):
        eg = EdgeGlow()
        snap = eg.get_system_pulse(real_slo=0.999980)
        assert snap.pulse == SystemPulse.GREEN

    def test_orange_from_slo_yellow_with_budget_warning(self):
        mock_budget = MagicMock()
        mock_budget.check_budget.return_value = MagicMock(
            to_dict=lambda: {"status": "warning"}
        )
        eg = EdgeGlow(budget_watchdog=mock_budget)
        snap = eg.get_system_pulse(real_slo=0.999900, error_budget_remaining=0.6)
        assert snap.pulse == SystemPulse.ORANGE

    def test_orange_from_red_slo(self):
        eg = EdgeGlow()
        snap = eg.get_system_pulse(real_slo=0.999500, error_budget_remaining=0.1)
        assert snap.pulse == SystemPulse.ORANGE

    def test_slo_calibrator_property(self):
        eg = EdgeGlow()
        assert isinstance(eg.slo_calibrator, SLOCalibrator)

    def test_slo_calibrator_custom(self):
        cal = SLOCalibrator(nominal_slo=0.99)
        eg = EdgeGlow(slo_calibrator=cal)
        assert eg.slo_calibrator.nominal_slo == 0.99

    def test_snapshot_contains_slo_field(self):
        eg = EdgeGlow()
        snap = eg.get_system_pulse(real_slo=0.999980)
        d = snap.to_dict()
        assert "slo" in d
        assert d["slo"]["nominal_slo"] == 0.999973

    def test_estimate_slo_from_workers(self):
        mock_phoenix = MagicMock()
        mock_phoenix.get_all_reports.return_value = {}
        eg = EdgeGlow(phoenix=mock_phoenix)
        snap = eg.get_system_pulse()
        assert isinstance(snap.pulse, SystemPulse)

    def test_calibrate_and_get_history(self):
        eg = EdgeGlow()
        for i in range(3):
            eg.get_system_pulse(real_slo=0.999973 - 0.000001 * i)
        assert len(eg.slo_calibrator.get_history()) == 3
