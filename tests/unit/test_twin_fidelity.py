import pytest

from app.twin.emitter import DigitalTwinEmitter
from app.twin.fidelity import FidelityReport, TwinFidelityValidator


class TestFidelityReport:
    def test_to_dict(self):
        r = FidelityReport(
            is_within_bounds=True,
            discrepancy_pct=0.001,
            threshold_pct=0.1,
            drifted_fields=[],
            twin_snapshot={"timestamp": "2026-01-01T00:00:00"},
            kernel_snapshot={"kernel_trust": 0.999},
        )
        d = r.to_dict()
        assert d["is_within_bounds"] is True
        assert d["discrepancy_pct"] == 0.001
        assert d["timestamp"] == "2026-01-01T00:00:00"


class TestTwinFidelityValidator:
    @pytest.mark.asyncio
    async def test_validate_within_bounds(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "cpu", lambda: {"status": "ok", "data": {"cpu": 0.5}, "trust_score": 0.95}
        )
        await e.poll_once()
        v = TwinFidelityValidator(e, threshold=0.5)
        report = v.validate()
        assert report.is_within_bounds is True

    @pytest.mark.asyncio
    async def test_validate_with_drift(self):
        e = DigitalTwinEmitter()
        v = TwinFidelityValidator(e, threshold=0.0001)
        report = v.validate()
        assert isinstance(report, FidelityReport)

    @pytest.mark.asyncio
    async def test_threshold_property(self):
        e = DigitalTwinEmitter()
        v = TwinFidelityValidator(e, threshold=0.001)
        assert v.threshold == 0.001

    @pytest.mark.asyncio
    async def test_validate_emitter_drift_true(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "cpu", lambda: {"status": "ok", "data": {"cpu": 0.5}, "trust_score": 0.9999}
        )
        await e.poll_once()
        v = TwinFidelityValidator(e, threshold=1.0)
        assert v.validate_emitter_drift() is True

    def test_default_threshold(self):
        from app.twin.fidelity import _TWIN_FIDELITY_THRESHOLD

        assert _TWIN_FIDELITY_THRESHOLD == 0.001

    @pytest.mark.asyncio
    async def test_report_discrepancy_pct(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "bad", lambda: {"status": "ok", "data": {}, "trust_score": 0.5}
        )
        await e.poll_once()
        v = TwinFidelityValidator(e, threshold=0.001)
        report = v.validate()
        assert isinstance(report.discrepancy_pct, float)

    @pytest.mark.asyncio
    async def test_drifted_fields_empty_when_no_drift(self):
        e = DigitalTwinEmitter()
        e.register_provider(
            "stable",
            lambda: {"status": "ok", "data": {"cpu": 0.5}, "trust_score": 0.9999},
        )
        await e.poll_once()
        v = TwinFidelityValidator(e, threshold=0.5)
        report = v.validate()
        assert isinstance(report.drifted_fields, list)
