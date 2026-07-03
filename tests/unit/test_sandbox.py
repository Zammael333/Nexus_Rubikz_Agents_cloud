from app.sandbox.runtime import SandboxLevel, SandboxProfile, SandboxRuntime


class TestSandboxProfile:
    def test_default_level_none(self):
        p = SandboxProfile(worker_id="test")
        assert p.level == SandboxLevel.NONE
        assert p.allowed_network is False
        assert p.read_only_fs is True

    def test_to_dict(self):
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.STRICT,
            allowed_paths=["/app/data"],
            allowed_commands=["curl"],
            allowed_network=True,
            memory_limit_mb=512,
            cpu_limit_cores=2.0,
            read_only_fs=False,
            timeout_seconds=60,
        )
        d = p.to_dict()
        assert d["worker_id"] == "w1"
        assert d["level"] == "strict"
        assert d["allowed_paths"] == ["/app/data"]
        assert d["allowed_commands"] == ["curl"]
        assert d["allowed_network"] is True
        assert d["memory_limit_mb"] == 512
        assert d["cpu_limit_cores"] == 2.0
        assert d["read_only_fs"] is False
        assert d["timeout_seconds"] == 60


class TestSandboxRuntime:
    def test_initial_profiles_count(self):
        rt = SandboxRuntime()
        assert rt.profile_count == 6

    def test_get_profile_known(self):
        rt = SandboxRuntime()
        profile = rt.get_profile("semantic_watchdog")
        assert profile.level == SandboxLevel.NONE

    def test_get_profile_unknown_returns_none_level(self):
        rt = SandboxRuntime()
        profile = rt.get_profile("nonexistent")
        assert profile.level == SandboxLevel.NONE
        assert profile.worker_id == "nonexistent"

    def test_set_profile(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="custom",
            level=SandboxLevel.STRICT,
            allowed_paths=["/tmp"],
            allowed_network=True,
        )
        rt.set_profile(p)
        retrieved = rt.get_profile("custom")
        assert retrieved.level == SandboxLevel.STRICT
        assert retrieved.allowed_network is True

    def test_validate_none_level_always_true(self):
        rt = SandboxRuntime()
        p = SandboxProfile(worker_id="w1", level=SandboxLevel.NONE)
        rt.set_profile(p)
        assert rt.validate_operation("w1", "file_access", path="/etc/passwd") is True
        assert rt.validate_operation("w1", "command", command="rm -rf /") is True
        assert rt.validate_operation("w1", "network") is True

    def test_validate_file_access_allowed(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.GVISOR,
            allowed_paths=["/app/data", "/tmp"],
        )
        rt.set_profile(p)
        assert (
            rt.validate_operation("w1", "file_access", path="/app/data/foo.txt") is True
        )

    def test_validate_file_access_denied(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.GVISOR,
            allowed_paths=["/app/data"],
        )
        rt.set_profile(p)
        assert rt.validate_operation("w1", "file_access", path="/etc/passwd") is False

    def test_validate_file_access_empty_allowed_list(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.GVISOR,
            allowed_paths=[],
        )
        rt.set_profile(p)
        assert rt.validate_operation("w1", "file_access", path="/app/data") is False

    def test_validate_command_allowed(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.CONTAINER,
            allowed_commands=["curl", "wget"],
        )
        rt.set_profile(p)
        assert (
            rt.validate_operation("w1", "command", command="curl https://example.com")
            is True
        )

    def test_validate_command_denied(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.CONTAINER,
            allowed_commands=["curl"],
        )
        rt.set_profile(p)
        assert rt.validate_operation("w1", "command", command="rm -rf /") is False

    def test_validate_network_allowed(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.CONTAINER,
            allowed_network=True,
        )
        rt.set_profile(p)
        assert rt.validate_operation("w1", "network") is True

    def test_validate_network_denied(self):
        rt = SandboxRuntime()
        p = SandboxProfile(
            worker_id="w1",
            level=SandboxLevel.GVISOR,
            allowed_network=False,
        )
        rt.set_profile(p)
        assert rt.validate_operation("w1", "network") is False

    def test_list_profiles(self):
        rt = SandboxRuntime()
        profiles = rt.list_profiles()
        assert len(profiles) == 6
        assert "semantic_watchdog" in profiles
        assert "inventory_worker" in profiles

    def test_default_profiles_have_correct_levels(self):
        rt = SandboxRuntime()
        assert rt.get_profile("inventory_worker").level == SandboxLevel.GVISOR
        assert rt.get_profile("scorpion_scanner").level == SandboxLevel.STRICT
        assert rt.get_profile("notification_dispatcher").level == SandboxLevel.CONTAINER
        assert rt.get_profile("watchdog_guardian").level == SandboxLevel.NONE

    def test_is_gvisor_available(self):
        rt = SandboxRuntime()
        assert isinstance(rt.is_gvisor_available(), bool)
