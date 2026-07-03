import os
import tempfile

from app.spiffe.manager import SpiffeConfig, SpiffeIdentity, SpiffeManager, SpiffeMode


class TestSpiffeIdentity:
    def test_short_id_from_spiffe(self):
        identity = SpiffeIdentity(
            worker_id="test_worker",
            spiffe_id="spiffe://nexus-rubykz.dev/worker/test_worker",
        )
        assert identity.short_id == "test_worker"

    def test_default_trust_domain(self):
        identity = SpiffeIdentity(worker_id="w", spiffe_id="spiffe://d/b")
        assert identity.trust_domain == "nexus-rubykz.dev"

    def test_default_mode_dev(self):
        identity = SpiffeIdentity(worker_id="w", spiffe_id="spiffe://d/b")
        assert identity.mode == SpiffeMode.DEV


class TestSpiffeManager:
    def test_initial_state(self):
        mgr = SpiffeManager()
        assert mgr.list_identities() == {}

    def test_register_worker_known(self):
        mgr = SpiffeManager()
        identity = mgr.register_worker("semantic_watchdog")
        assert (
            identity.spiffe_id == "spiffe://nexus-rubykz.dev/worker/semantic_watchdog"
        )
        assert identity.worker_id == "semantic_watchdog"

    def test_register_worker_unknown(self):
        mgr = SpiffeManager()
        identity = mgr.register_worker("custom_worker")
        assert "custom_worker" in identity.spiffe_id

    def test_register_worker_custom_spiffe(self):
        mgr = SpiffeManager()
        identity = mgr.register_worker("my_worker", "spiffe://custom.domain/worker/my")
        assert identity.spiffe_id == "spiffe://custom.domain/worker/my"

    def test_get_identity_found(self):
        mgr = SpiffeManager()
        mgr.register_worker("semantic_watchdog")
        identity = mgr.get_identity("semantic_watchdog")
        assert identity is not None
        assert identity.worker_id == "semantic_watchdog"

    def test_get_identity_not_found(self):
        mgr = SpiffeManager()
        assert mgr.get_identity("nonexistent") is None

    def test_register_all_workers(self):
        mgr = SpiffeManager()
        identities = mgr.register_all_workers()
        assert len(identities) == 10
        assert "semantic_watchdog" in identities
        assert "watchdog_guardian" in identities
        assert "phoenix_protocol" in identities

    def test_get_all_spiffe_ids(self):
        mgr = SpiffeManager()
        mgr.register_all_workers()
        ids = mgr.get_all_spiffe_ids()
        assert len(ids) == 10
        assert all(id.startswith("spiffe://") for id in ids)

    def test_build_registration_entries(self):
        mgr = SpiffeManager()
        mgr.register_all_workers()
        entries = mgr.build_registration_entries()
        assert len(entries) == 10
        for entry in entries:
            assert "spiffe_id" in entry
            assert "parent_id" in entry
            assert "selectors" in entry
            assert "ttl" in entry

    def test_to_dict(self):
        mgr = SpiffeManager()
        mgr.register_worker("test_worker")
        d = mgr.to_dict()
        assert d["mode"] == "dev"
        assert "identities" in d
        assert "test_worker" in d["identities"]

    def test_generate_spire_server_config(self):
        mgr = SpiffeManager()
        config = mgr.generate_spire_server_config()
        assert "spire_server" in config.lower() or "server {" in config
        assert "nexus-rubykz" in config

    def test_generate_spire_agent_config(self):
        mgr = SpiffeManager()
        config = mgr.generate_spire_agent_config()
        assert "spire_agent" in config.lower() or "agent {" in config
        assert "nexus-rubykz" in config

    def test_generate_spire_server_config_writes_file(self):
        mgr = SpiffeManager()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            path = f.name
        try:
            mgr.generate_spire_server_config(output_path=path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "server {" in content
        finally:
            os.unlink(path)

    def test_generate_spire_agent_config_writes_file(self):
        mgr = SpiffeManager()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            path = f.name
        try:
            mgr.generate_spire_agent_config(output_path=path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "agent {" in content
        finally:
            os.unlink(path)

    def test_dev_mode_default(self):
        mgr = SpiffeManager()
        assert mgr._mode == SpiffeMode.DEV

    def test_production_mode(self):
        config = SpiffeConfig(mode=SpiffeMode.PRODUCTION)
        mgr = SpiffeManager(config=config)
        assert mgr._mode == SpiffeMode.PRODUCTION
