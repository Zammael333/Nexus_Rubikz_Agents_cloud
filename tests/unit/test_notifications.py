from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.notifications import NotificationChannel, NotificationDispatcher


class TestNotificationDispatcher:
    @pytest.fixture
    def log_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            path = f.name
        yield path
        os.unlink(path)

    def test_dispatch_local_log(self, log_file):
        dispatcher = NotificationDispatcher(log_file=log_file)
        ok = dispatcher.dispatch("TEST_EVENT", {"key": "value"}, source="test")
        assert ok is True
        assert dispatcher.dispatch_count == 1
        assert dispatcher.failure_count == 0
        with open(log_file) as f:
            content = f.read()
        assert "TEST_EVENT" in content
        assert "key" in content

    def test_dispatch_webhook_success(self):
        dispatcher = NotificationDispatcher(
            webhook_url="http://localhost:9999/hook",
        )
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__.return_value.status = 200
            mock_urlopen.return_value = mock_response
            ok = dispatcher.dispatch("WEBHOOK_TEST", {"msg": "hello"})
        assert ok is True

    def test_dispatch_webhook_failure(self):
        dispatcher = NotificationDispatcher(
            webhook_url="http://localhost:9999/hook",
        )
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            ok = dispatcher.dispatch("WEBHOOK_FAIL", {"msg": "fail"})
        assert ok is True
        assert dispatcher.failure_count == 1

    def test_as_bus_hook_critical(self):
        dispatcher = NotificationDispatcher(log_file="/dev/null")
        hook = dispatcher.as_bus_hook()

        mock_event = MagicMock()
        mock_event.priority.name = "CRITICAL"
        mock_event.type = "TEST_EVENT"
        mock_event.payload = {"key": "val"}
        mock_event.source = "test"

        with patch.object(dispatcher, "dispatch") as mock_dispatch:
            hook([mock_event])
        mock_dispatch.assert_called_once_with(
            event_type="TEST_EVENT",
            payload={"key": "val"},
            source="test",
        )

    def test_as_bus_hook_non_critical(self):
        dispatcher = NotificationDispatcher(log_file="/dev/null")
        hook = dispatcher.as_bus_hook()

        mock_event = MagicMock()
        mock_event.priority.name = "NORMAL"

        with patch.object(dispatcher, "dispatch") as mock_dispatch:
            hook([mock_event])
        mock_dispatch.assert_not_called()

    def test_add_channel(self):
        channel = NotificationChannel(
            name="test_channel",
            dispatch_fn=lambda n: True,
        )
        dispatcher = NotificationDispatcher()
        dispatcher.add_channel(channel)
        assert dispatcher.dispatch("TEST", {}) is True

    def test_add_channel_failure(self):
        channel = NotificationChannel(
            name="failing_channel",
            dispatch_fn=lambda n: False,
        )
        dispatcher = NotificationDispatcher()
        dispatcher.add_channel(channel)
        with patch.object(dispatcher, "_dispatch_local_log", return_value=True):
            ok = dispatcher.dispatch("TEST", {})
        assert ok is True
