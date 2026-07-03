from __future__ import annotations

import logging

from app.disclosure.logger import (
    ProgressiveDisclosure,
    TrustAdaptiveLevel,
    trust_to_level,
)


class TestTrustAdaptiveLevel:
    def test_trust_to_level_debug(self):
        assert trust_to_level(0.0) == TrustAdaptiveLevel.DEBUG
        assert trust_to_level(0.1) == TrustAdaptiveLevel.DEBUG
        assert trust_to_level(0.29) == TrustAdaptiveLevel.DEBUG

    def test_trust_to_level_info(self):
        assert trust_to_level(0.3) == TrustAdaptiveLevel.INFO
        assert trust_to_level(0.5) == TrustAdaptiveLevel.INFO
        assert trust_to_level(0.59) == TrustAdaptiveLevel.INFO

    def test_trust_to_level_warn(self):
        assert trust_to_level(0.6) == TrustAdaptiveLevel.WARN
        assert trust_to_level(0.8) == TrustAdaptiveLevel.WARN
        assert trust_to_level(0.89) == TrustAdaptiveLevel.WARN

    def test_trust_to_level_error(self):
        assert trust_to_level(0.9) == TrustAdaptiveLevel.ERROR
        assert trust_to_level(1.0) == TrustAdaptiveLevel.ERROR

    def test_trust_to_level_below_zero(self):
        assert trust_to_level(-1.0) == TrustAdaptiveLevel.DEBUG


class TestProgressiveDisclosure:
    def test_init_defaults(self):
        pd = ProgressiveDisclosure(worker_id="w1")
        assert pd.worker_id == "w1"
        assert pd.trust_score == 1.0
        assert pd.effective_level == logging.ERROR

    def test_init_custom_trust(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.5)
        assert pd.trust_score == 0.5
        assert pd.effective_level == logging.INFO

    def test_update_trust(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=1.0)
        pd.update_trust(0.2)
        assert pd.trust_score == 0.2
        assert pd.effective_level == logging.DEBUG

    def test_update_trust_clamps_below_zero(self):
        pd = ProgressiveDisclosure(worker_id="w1")
        pd.update_trust(-0.5)
        assert pd.trust_score == 0.0

    def test_update_trust_clamps_above_one(self):
        pd = ProgressiveDisclosure(worker_id="w1")
        pd.update_trust(1.5)
        assert pd.trust_score == 1.0

    def test_is_enabled_for_disabled(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=1.0)
        pd.set_enabled(False)
        assert pd.is_enabled_for(logging.ERROR) is False

    def test_is_enabled_for_error_at_high_trust(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=1.0)
        assert pd.is_enabled_for(logging.ERROR) is True
        assert pd.is_enabled_for(logging.WARN) is False
        assert pd.is_enabled_for(logging.INFO) is False
        assert pd.is_enabled_for(logging.DEBUG) is False

    def test_is_enabled_for_debug_at_low_trust(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.0)
        assert pd.is_enabled_for(logging.ERROR) is True
        assert pd.is_enabled_for(logging.WARN) is True
        assert pd.is_enabled_for(logging.INFO) is True
        assert pd.is_enabled_for(logging.DEBUG) is True

    def test_is_enabled_for_info_at_mid_trust(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.5)
        assert pd.is_enabled_for(logging.ERROR) is True
        assert pd.is_enabled_for(logging.WARN) is True
        assert pd.is_enabled_for(logging.INFO) is True
        assert pd.is_enabled_for(logging.DEBUG) is False

    def test_debug_gated(self, caplog):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.0)
        with caplog.at_level(logging.DEBUG):
            pd.debug("test msg")
            assert "[w1] test msg" in caplog.text

    def test_debug_suppressed(self, caplog):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=1.0)
        with caplog.at_level(logging.DEBUG):
            pd.debug("should not appear")
            assert "should not appear" not in caplog.text

    def test_error_always_shows(self, caplog):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=1.0)
        with caplog.at_level(logging.ERROR):
            pd.error("critical")
            assert "[w1] critical" in caplog.text

    def test_info_gated_at_warn_level(self, caplog):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.7)
        with caplog.at_level(logging.DEBUG):
            pd.info("should be suppressed")
            pd.warning("should show")
            assert "should be suppressed" not in caplog.text
            assert "should show" in caplog.text

    def test_set_enabled(self):
        pd = ProgressiveDisclosure(worker_id="w1")
        assert pd._enabled is True
        pd.set_enabled(False)
        assert pd._enabled is False

    def test_to_dict(self):
        pd = ProgressiveDisclosure(worker_id="w1", trust_score=0.4)
        d = pd.to_dict()
        assert d["worker_id"] == "w1"
        assert d["trust_score"] == 0.4
        assert d["effective_level"] == "INFO"
        assert d["enabled"] is True
