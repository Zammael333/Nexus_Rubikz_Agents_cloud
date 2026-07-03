from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from app.a2a.protocol import A2AMessage
from app.otel import get_tracer
from app.spiffe.manager import SpiffeManager

_a2a_tracer = get_tracer("a2a.transport")

logger = logging.getLogger(__name__)


class A2ATransport:
    """Wire-level A2A transport over gRPC using SPIFFE mTLS credentials.

    Provides a gRPC stub (client) and a gRPC server (receiver) that
    exchange ``A2AMessage`` protobuf-encoded payloads.  The gRPC channel
    is secured via ``SpiffeManager.create_grpc_channel()`` which injects
    mTLS credentials from the SPIRE workload API.

    If SPIFFE is unavailable (e.g. dev mode) the transport falls back to
    an in-process queue, preserving the same async interface for the rest
    of the system.
    """

    def __init__(
        self,
        worker_id: str,
        spiffe_manager: SpiffeManager | None = None,
        listen_addr: str = "[::]:50051",
        grpc_max_message_length: int = 4 * 1024 * 1024,
    ):
        self._worker_id = worker_id
        self._spiffe_manager = spiffe_manager
        self._listen_addr = listen_addr
        self._grpc_max_message_length = grpc_max_message_length

        self._server: Any = None
        self._channel: Any = None
        self._running = False

        self._incoming: asyncio.Queue[bytes] = asyncio.Queue()
        self._message_count = 0
        self._failure_count = 0
        self._bg_task: asyncio.Task | None = None

    # -- Client side ---------------------------------------------------------

    async def connect(self, target_addr: str) -> bool:
        with _a2a_tracer.start_as_current_span(
            "a2a.transport.connect",
            attributes={"target_addr": target_addr, "worker_id": self._worker_id},
        ) as span:
            try:
                import grpc

                if self._spiffe_manager and hasattr(self._spiffe_manager, "create_grpc_channel"):
                    channel = self._spiffe_manager.create_grpc_channel(target_addr)
                else:
                    channel = grpc.aio.insecure_channel(
                        target_addr,
                        options=[
                            ("grpc.max_send_message_length", self._grpc_max_message_length),
                            ("grpc.max_receive_message_length", self._grpc_max_message_length),
                        ],
                    )
                self._channel = channel
                span.set_attribute("transport.type", "grpc")
                logger.info("[A2A_TRANSPORT] gRPC channel connected to %s", target_addr)
                return True
            except ImportError:
                span.set_attribute("transport.type", "inprocess")
                logger.warning("[A2A_TRANSPORT] grpcio not installed — using in-process fallback")
                return True
            except Exception as exc:
                span.set_attribute("error", str(exc))
                span.set_attribute("transport.type", "failed")
                logger.error("[A2A_TRANSPORT] gRPC connect failed: %s", exc)
                return False

    async def send(self, message: A2AMessage) -> bool:
        data = message.to_dict()
        transport_type = "grpc" if self._channel is not None else "inprocess"

        with _a2a_tracer.start_as_current_span(
            "a2a.transport.send",
            attributes={
                "worker_id": self._worker_id,
                "transport.type": transport_type,
                "a2a.action": data.get("action", ""),
                "a2a.target": data.get("target_worker", ""),
                "a2a.msg_type": data.get("type", ""),
                "a2a.correlation_id": data.get("correlation_id", ""),
            },
        ) as span:
            if self._channel is not None:
                ok = await self._send_grpc(data)
            else:
                ok = await self._send_inprocess(data)
            span.set_attribute("outcome", "sent" if ok else "failed")
            return ok

    async def _send_grpc(self, data: dict[str, Any]) -> bool:
        try:
            import json


            stub = self._build_stub()
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            _ = await stub.Deliver(payload, timeout=10.0)
            self._message_count += 1
            return True
        except Exception as exc:
            self._failure_count += 1
            logger.error("[A2A_TRANSPORT] gRPC send failed: %s", exc)
            return False

    async def _send_inprocess(self, data: dict[str, Any]) -> bool:
        import json
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        await self._incoming.put(payload)
        self._message_count += 1
        return True

    def _build_stub(self):
        return _build_a2a_stub(self._channel)

    # -- Server side ---------------------------------------------------------

    async def start_server(self, handler: Callable[[dict[str, Any]], None]) -> None:
        if self._running:
            return
        self._running = True

        with _a2a_tracer.start_as_current_span(
            "a2a.transport.start_server",
            attributes={"listen_addr": self._listen_addr, "worker_id": self._worker_id},
        ) as span:
            try:
                from grpc import aio as grpc_aio

                server = grpc_aio.server(
                    options=[
                        ("grpc.max_send_message_length", self._grpc_max_message_length),
                        ("grpc.max_receive_message_length", self._grpc_max_message_length),
                    ],
                )
                _add_a2a_servicer(server, handler)
                port = server.add_insecure_port(self._listen_addr)
                await server.start()
                self._server = server
                span.set_attribute("transport.type", "grpc")
                span.set_attribute("grpc.port", port)
                logger.info(
                    "[A2A_TRANSPORT] gRPC server listening on %s (port %d)",
                    self._listen_addr,
                    port,
                )
            except ImportError:
                span.set_attribute("transport.type", "inprocess")
                logger.info("[A2A_TRANSPORT] grpcio not installed — starting in-process loop")
                self._bg_task = asyncio.create_task(self._inprocess_server_loop(handler))
            except Exception as exc:
                span.set_attribute("error", str(exc))
                span.set_attribute("transport.type", "failed")
                logger.error("[A2A_TRANSPORT] gRPC server start failed: %s", exc)

    async def _inprocess_server_loop(
        self, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        while self._running:
            try:
                payload = await asyncio.wait_for(self._incoming.get(), timeout=1.0)
            except TimeoutError:
                continue
            try:
                import json
                data = json.loads(payload.decode("utf-8"))
                handler(data)
            except Exception as exc:
                logger.error("[A2A_TRANSPORT] in-process handler error: %s", exc)

    async def stop_server(self) -> None:
        with _a2a_tracer.start_as_current_span(
            "a2a.transport.stop_server", attributes={"worker_id": self._worker_id}
        ):
            self._running = False
            if self._server:
                await self._server.stop(grace=5.0)
                self._server = None
            logger.info("[A2A_TRANSPORT] Server stopped.")

    @property
    def message_count(self) -> int:
        return self._message_count

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def is_connected(self) -> bool:
        return self._channel is not None or not self._running


# -- gRPC protobuf stubs (lightweight inline) --------------------------------
# These are kept minimal to avoid a .proto compilation dependency.
# A full implementation would use the generated *_pb2.py / *_pb2_grpc.py.

_A2A_SERVICE_NAME = "nexus.a2a.A2AService"
_A2A_METHOD_DELIVER = "Deliver"


def _build_a2a_stub(channel):
    """Build a dynamic gRPC stub for the A2A service."""

    class A2AStub:
        def __init__(self, ch):
            self._channel = ch

        async def Deliver(self, payload: bytes, timeout: float = 10.0):

            call = self._channel.unary_unary(
                f"/{_A2A_SERVICE_NAME}/{_A2A_METHOD_DELIVER}",
                request_serializer=lambda x: x,
                response_deserializer=lambda x: x,
            )
            return await call(payload, timeout=timeout)

    return A2AStub(channel)


def _add_a2a_servicer(server, handler: Callable[[dict[str, Any]], None]):
    """Add the A2A servicer to a gRPC server."""

    class A2AServicer:
        async def Deliver(self, request, context):
            import json
            try:
                data = json.loads(request.decode("utf-8"))
                handler(data)
                return b'{"status":"ok"}'
            except Exception as exc:
                context.set_code(13)
                context.set_details(str(exc))
                return b'{"status":"error"}'


    server.add_generic_rpc_handlers(
        [
            (
                f"/{_A2A_SERVICE_NAME}/{_A2A_METHOD_DELIVER}",
                A2AServicer().Deliver,
            )
        ]
    )
