# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Notification Dispatcher (Paso 28)
# Dispatches CRITICAL events to configurable notification channels.

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

CRITICAL_TAG = settings.notification_critical_tag


@dataclass
class NotificationChannel:
    """A named notification channel with a dispatch callback."""

    name: str
    dispatch_fn: Callable[[dict[str, Any]], bool]
    enabled: bool = True


class NotificationDispatcher:
    """Dispatches CRITICAL events to configured notification channels.

    Built-in channels:
      - ``local_log``: Writes CRITICAL events to a dedicated log with
        ``[CRITICAL_NOTIFICATION]`` tag.
      - ``webhook``: Sends HTTP POST with JSON payload to a configured URL.

    Can also be registered as the ``remote_delivery_hook`` on AsyncEventBus
    to receive events inline during flush.

    Args:
        webhook_url: Optional URL for the webhook channel.
        log_file: Path for the critical notification log.
        channels: Additional custom channels.
    """

    def __init__(
        self,
        webhook_url: str | None = None,
        log_file: str = "nexus_critical_notifications.log",
        channels: list[NotificationChannel] | None = None,
    ):
        self._log_file = log_file
        self._webhook_url = webhook_url
        self._channels: list[NotificationChannel] = []
        self._dispatch_count = 0
        self._failure_count = 0

        # Built-in: local log channel (always present)
        self._channels.append(
            NotificationChannel(
                name="local_log",
                dispatch_fn=self._dispatch_local_log,
            )
        )

        # Built-in: webhook channel (if URL provided)
        if webhook_url:
            self._channels.append(
                NotificationChannel(
                    name="webhook",
                    dispatch_fn=self._dispatch_webhook,
                )
            )

        # Custom channels
        if channels:
            self._channels.extend(channels)

    # -- Public API ---------------------------------------------------------

    def dispatch(
        self, event_type: str, payload: dict[str, Any], source: str = "system"
    ) -> bool:
        """Dispatch a notification to all enabled channels.

        Returns True if at least one channel succeeded.
        """
        notification = {
            "event_type": event_type,
            "payload": payload,
            "source": source,
            "dispatched_at": datetime.now(UTC).isoformat(),
            "severity": "CRITICAL",
        }

        any_success = False
        for channel in self._channels:
            if not channel.enabled:
                continue
            try:
                ok = channel.dispatch_fn(notification)
                if ok:
                    any_success = True
                    logger.info(
                        f"[NOTIFICATIONS] Dispatched to '{channel.name}': {event_type}"
                    )
                else:
                    self._failure_count += 1
                    logger.warning(
                        f"[NOTIFICATIONS] Channel '{channel.name}' returned False for {event_type}"
                    )
            except Exception as e:
                self._failure_count += 1
                logger.error(f"[NOTIFICATIONS] Channel '{channel.name}' error: {e}")

        if any_success:
            self._dispatch_count += 1

        return any_success

    def as_bus_hook(self) -> Callable:
        """Return a callable suitable for AsyncEventBus.remote_delivery_hook.

        The hook filters for CRITICAL events and dispatches them.
        """

        def hook(events: list) -> None:
            for event in events:
                # BusEvent has .priority and .type attributes
                priority_name = getattr(getattr(event, "priority", None), "name", "")
                if priority_name == "CRITICAL":
                    self.dispatch(
                        event_type=event.type,
                        payload=event.payload,
                        source=event.source,
                    )

        return hook

    def add_channel(self, channel: NotificationChannel) -> None:
        """Register an additional notification channel."""
        self._channels.append(channel)

    @property
    def dispatch_count(self) -> int:
        return self._dispatch_count

    @property
    def failure_count(self) -> int:
        return self._failure_count

    # -- Built-in channel implementations -----------------------------------

    def _dispatch_local_log(self, notification: dict[str, Any]) -> bool:
        """Write the notification to a dedicated log file."""
        try:
            line = (
                f"{CRITICAL_TAG} [{notification['event_type']}] "
                f"source={notification['source']} "
                f"at={notification['dispatched_at']} "
                f"payload={json.dumps(notification['payload'], ensure_ascii=False)}\n"
            )
            with open(self._log_file, "a") as f:
                f.write(line)
            return True
        except OSError as e:
            logger.error(f"[NOTIFICATIONS] Local log write failed: {e}")
            return False

    def _dispatch_webhook(self, notification: dict[str, Any]) -> bool:
        """Send an HTTP POST with JSON payload to the configured webhook URL."""
        if not self._webhook_url:
            return False
        try:
            data = json.dumps(notification, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status < 400
        except (urllib.error.URLError, OSError) as e:
            logger.error(f"[NOTIFICATIONS] Webhook dispatch failed: {e}")
            return False
