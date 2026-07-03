from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class A2AMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    COMMAND = "command"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"


@dataclass
class A2AMessage:
    type: A2AMessageType
    source_worker: str
    target_worker: str
    action: str
    payload: dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reply_to: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ttl_seconds: float = 30.0
    trust_threshold: float = 0.0

    def __post_init__(self) -> None:
        from app.config import settings
        if abs(self.ttl_seconds - 30.0) < 1e-9 and settings.a2a_ttl_seconds != 30.0:
            object.__setattr__(self, "ttl_seconds", settings.a2a_ttl_seconds)
        if abs(self.trust_threshold) < 1e-9 and settings.a2a_trust_threshold != 0.0:
            object.__setattr__(self, "trust_threshold", settings.a2a_trust_threshold)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "source_worker": self.source_worker,
            "target_worker": self.target_worker,
            "action": self.action,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp,
            "ttl_seconds": self.ttl_seconds,
            "trust_threshold": self.trust_threshold,
        }


@dataclass
class A2AResponse:
    correlation_id: str
    success: bool
    payload: dict[str, Any]
    error: str = ""
    source_worker: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "success": self.success,
            "payload": self.payload,
            "error": self.error,
            "source_worker": self.source_worker,
            "timestamp": self.timestamp,
        }


HandlerFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class A2AProtocol:
    def __init__(
        self,
        worker_id: str,
        bus=None,
        trust_scorer=None,
        spiffe_manager=None,
        default_timeout: float = 10.0,
        max_retries: int = 2,
    ):
        self._worker_id = worker_id
        self._bus = bus
        self._trust_scorer = trust_scorer
        self._spiffe_manager = spiffe_manager
        self._default_timeout = default_timeout
        self._max_retries = max_retries

        self._handlers: dict[str, HandlerFn] = {}
        self._pending: dict[str, tuple[asyncio.Future, float]] = {}

        self._running = False
        self._consumer_task: asyncio.Task | None = None

        self._message_count = 0
        self._failure_count = 0
        self._background_tasks: set[asyncio.Task] = set()

    def register_handler(self, action: str, handler: HandlerFn) -> None:
        self._handlers[action] = handler
        logger.info(f"[A2A] Handler registered for action '{action}'.")

    def unregister_handler(self, action: str) -> None:
        self._handlers.pop(action, None)
        logger.info(f"[A2A] Handler '{action}' unregistered.")

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume_loop())
        logger.info(f"[A2A] Protocol started for worker '{self._worker_id}'.")

    async def stop(self) -> None:
        self._running = False
        if self._consumer_task:
            try:
                await asyncio.wait_for(self._consumer_task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                logger.warning("[A2A] Consumer did not stop cleanly.")
        for _corr_id, (future, _) in list(self._pending.items()):
            if not future.done():
                future.set_exception(TimeoutError("Protocol stopped"))
        self._pending.clear()

    async def send_message(self, message: A2AMessage) -> bool:
        event_type = f"a2a.{message.type.value}"
        payload = message.to_dict()
        if self._bus:
            return await self._bus.emit(event_type, payload, source=self._worker_id)
        logger.warning("[A2A] No bus configured, message not sent.")
        return False

    async def send_request(
        self,
        target_worker: str,
        action: str,
        payload: dict[str, Any],
        timeout: float | None = None,
        trust_threshold: float = 0.0,
    ) -> A2AResponse:
        timeout = timeout or self._default_timeout
        message = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker=self._worker_id,
            target_worker=target_worker,
            action=action,
            payload=payload,
            reply_to=self._worker_id,
            trust_threshold=trust_threshold,
        )
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        deadline = time.time() + timeout
        self._pending[message.correlation_id] = (future, deadline)

        sent = await self.send_message(message)
        if not sent:
            self._pending.pop(message.correlation_id, None)
            self._failure_count += 1
            return A2AResponse(
                correlation_id=message.correlation_id,
                success=False,
                payload={},
                error="Failed to send request",
                source_worker="",
            )

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except TimeoutError:
            self._pending.pop(message.correlation_id, None)
            self._failure_count += 1
            return A2AResponse(
                correlation_id=message.correlation_id,
                success=False,
                payload={},
                error=f"Timeout after {timeout}s",
                source_worker="",
            )

    async def send_response(
        self, request_msg: A2AMessage, response: A2AResponse
    ) -> bool:
        message = A2AMessage(
            type=A2AMessageType.RESPONSE,
            source_worker=self._worker_id,
            target_worker=request_msg.reply_to or request_msg.source_worker,
            action=request_msg.action,
            payload=response.to_dict(),
            correlation_id=request_msg.correlation_id,
        )
        return await self.send_message(message)

    async def send_command(
        self,
        target_worker: str,
        action: str,
        payload: dict[str, Any],
    ) -> bool:
        message = A2AMessage(
            type=A2AMessageType.COMMAND,
            source_worker=self._worker_id,
            target_worker=target_worker,
            action=action,
            payload=payload,
        )
        return await self.send_message(message)

    async def broadcast(
        self,
        action: str,
        payload: dict[str, Any],
        target_workers: list[str],
    ) -> list[str]:
        sent: list[str] = []
        for worker in target_workers:
            message = A2AMessage(
                type=A2AMessageType.BROADCAST,
                source_worker=self._worker_id,
                target_worker=worker,
                action=action,
                payload=payload,
            )
            ok = await self.send_message(message)
            if ok:
                sent.append(worker)
        return sent

    def handle_bus_event(self, event) -> None:
        if not hasattr(event, "type") or not str(getattr(event, "type", "")).startswith(
            "a2a."
        ):
            return
        try:
            data = event.payload
            if not isinstance(data, dict):
                return

            target = data.get("target_worker", "")
            if target and target != self._worker_id and target != "*":
                return

            source = data.get("source_worker", "")
            if not source:
                return

            if self._spiffe_manager:
                identity = self._spiffe_manager.get_identity(source)
                if identity is None:
                    logger.warning(f"[A2A] Unknown source worker: {source}")
                    self._failure_count += 1
                    return

            trust_threshold = data.get("trust_threshold", 0.0)
            if trust_threshold > 0 and source and self._trust_scorer:
                report = self._trust_scorer.get_latest(source)
                if report and report.overall_score < trust_threshold:
                    logger.warning(
                        f"[A2A] Trust too low for '{source}': "
                        f"{report.overall_score:.2f} < {trust_threshold}"
                    )
                    self._failure_count += 1
                    return

            msg_type_str = data.get("type", "")
            try:
                msg_type = A2AMessageType(msg_type_str)
            except ValueError:
                logger.warning(f"[A2A] Unknown message type: {msg_type_str}")
                self._failure_count += 1
                return

            action = data.get("action", "")
            correlation_id = data.get("correlation_id", "")

            if msg_type == A2AMessageType.REQUEST:
                self._background_tasks.add(
                    asyncio.create_task(self._handle_request(source, action, data))
                )
            elif msg_type == A2AMessageType.RESPONSE:
                self._handle_response(correlation_id, data)
            elif msg_type == A2AMessageType.COMMAND:
                self._background_tasks.add(
                    asyncio.create_task(self._handle_command(source, action, data))
                )

            self._message_count += 1

        except Exception as e:
            self._failure_count += 1
            logger.error(f"[A2A] Error handling bus event: {e}")

    async def _handle_request(
        self, source: str, action: str, data: dict[str, Any]
    ) -> None:
        handler = self._handlers.get(action)
        if handler is None:
            logger.warning(f"[A2A] No handler for action '{action}' from '{source}'.")
            return
        try:
            result = await handler(data.get("payload", {}))

            reply_to = data.get("reply_to", "")
            if reply_to:
                response = A2AResponse(
                    correlation_id=data.get("correlation_id", ""),
                    success=True,
                    payload=(
                        result if isinstance(result, dict) else {"result": result}
                    ),
                    source_worker=self._worker_id,
                )
                await self._send_response_inner(reply_to, action, response)
        except Exception as e:
            logger.error(f"[A2A] Handler '{action}' error: {e}")
            reply_to = data.get("reply_to", "")
            if reply_to:
                response = A2AResponse(
                    correlation_id=data.get("correlation_id", ""),
                    success=False,
                    payload={},
                    error=str(e),
                    source_worker=self._worker_id,
                )
                await self._send_response_inner(reply_to, action, response)

    async def _handle_command(
        self, source: str, action: str, data: dict[str, Any]
    ) -> None:
        handler = self._handlers.get(action)
        if handler is None:
            logger.warning(f"[A2A] No handler for command '{action}' from '{source}'.")
            return
        try:
            await handler(data.get("payload", {}))
        except Exception as e:
            logger.error(f"[A2A] Command handler '{action}' error: {e}")

    async def _send_response_inner(
        self, target_worker: str, action: str, response: A2AResponse
    ) -> None:
        message = A2AMessage(
            type=A2AMessageType.RESPONSE,
            source_worker=self._worker_id,
            target_worker=target_worker,
            action=action,
            payload=response.to_dict(),
            correlation_id=response.correlation_id,
        )
        await self.send_message(message)

    def _handle_response(self, correlation_id: str, data: dict[str, Any]) -> None:
        entry = self._pending.pop(correlation_id, None)
        if entry is None:
            return
        future, _ = entry
        if future.done():
            return
        response_payload = data.get("payload", {})
        response = A2AResponse(
            correlation_id=correlation_id,
            success=response_payload.get("success", False),
            payload=response_payload.get("payload", {}),
            error=response_payload.get("error", ""),
            source_worker=response_payload.get("source_worker", ""),
            timestamp=response_payload.get("timestamp", ""),
        )
        future.set_result(response)

    async def _consume_loop(self) -> None:
        while self._running:
            await asyncio.sleep(0.5)
            now = time.time()
            stale = [
                corr_id
                for corr_id, (_, deadline) in self._pending.items()
                if now > deadline
            ]
            for corr_id in stale:
                future, _ = self._pending.pop(corr_id, (None, 0))
                if future and not future.done():
                    future.set_exception(TimeoutError("Request timed out"))

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def handlers(self) -> dict[str, HandlerFn]:
        return dict(self._handlers)

    @property
    def worker_id(self) -> str:
        return self._worker_id
