from app.sandbox.runtime import (
    AnomalyRecord,
    SandboxLevel,
    SandboxProfile,
    SandboxRuntime,
)


class TestAnomalyRecord:
    def test_defaults(self):
        r = AnomalyRecord(
            worker_id="w1", anomaly_type="timeout", details="exec exceeded 30s"
        )
        assert r.worker_id == "w1"
        assert r.anomaly_type == "timeout"
        assert r.details == "exec exceeded 30s"
        assert isinstance(r.timestamp, float)

    def test_to_dict(self):
        r = AnomalyRecord(worker_id="w1", anomaly_type="high_memory", details="512MB")
        d = r.to_dict()
        assert d["worker_id"] == "w1"
        assert d["anomaly_type"] == "high_memory"


class TestSandboxAnomaly:
    def test_record_anomaly(self):
        rt = SandboxRuntime()
        r = rt.record_anomaly("w1", "timeout", "exec exceeded 30s")
        assert r.worker_id == "w1"
        assert len(rt.get_anomalies("w1")) == 1

    def test_anomaly_count_within_window(self):
        rt = SandboxRuntime()
        for _ in range(3):
            rt.record_anomaly("w2", "cpu_spike")
        assert rt.anomaly_count("w2") == 3

    def test_anomaly_count_empty(self):
        rt = SandboxRuntime()
        assert rt.anomaly_count("nonexistent") == 0

    def test_all_anomalies(self):
        rt = SandboxRuntime()
        rt.record_anomaly("w1", "timeout")
        rt.record_anomaly("w2", "memory")
        all_a = rt.all_anomalies()
        assert "w1" in all_a
        assert "w2" in all_a
        assert len(all_a["w1"]) == 1

    def test_auto_sandbox_below_threshold(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.NONE)
        rt.set_profile(p)
        result = rt.auto_sandbox("w1", "test", details="anomaly 1")
        assert result is None
        assert rt.get_profile("w1").level == SandboxLevel.NONE

    def test_auto_sandbox_escalates(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.NONE)
        rt.set_profile(p)
        for _ in range(3):
            rt.auto_sandbox("w1", "test", details="trigger")
        assert rt.get_profile("w1").level == SandboxLevel.GVISOR

    def test_auto_sandbox_multiple_escalations(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.NONE)
        rt.set_profile(p)
        for _ in range(5):
            rt.auto_sandbox("w1", "test", details="escalate")
        assert rt.get_profile("w1").level == SandboxLevel.STRICT

    def test_auto_sandbox_to_strict(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.NONE)
        rt.set_profile(p)
        for _ in range(10):
            rt.auto_sandbox("w1", "test", details="max")
        assert rt.get_profile("w1").level == SandboxLevel.STRICT

    def test_self_isolate(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.NONE,
            allowed_paths=["/tmp"],
            allowed_commands=["curl"],
            allowed_network=True,
            timeout_seconds=30,
        )
        rt.set_profile(p)
        isolated = rt.self_isolate("w1", "admin_override")
        assert isolated.level == SandboxLevel.STRICT
        assert isolated.allowed_paths == []
        assert isolated.allowed_commands == []
        assert isolated.allowed_network is False
        assert isolated.read_only_fs is True

    def test_reset_anomalies(self):
        rt = SandboxRuntime()
        rt.record_anomaly("w1", "timeout")
        assert len(rt.get_anomalies("w1")) == 1
        rt.reset_anomalies("w1")
        assert len(rt.get_anomalies("w1")) == 0

    def test_auto_sandbox_stays_strict(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.STRICT)
        rt.set_profile(p)
        for _ in range(5):
            rt.auto_sandbox("w1", "test")
        assert rt.get_profile("w1").level == SandboxLevel.STRICT
