import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.a2a.protocol import A2AMessage, A2AMessageType, A2AProtocol, A2AResponse


class FakeEvent:
    def __init__(self, event_type: str, payload: dict):
        self.type = event_type
        self.payload = payload


class TestA2AMessage:
    def test_defaults(self):
        msg = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker="w1",
            target_worker="w2",
            action="ping",
            payload={},
        )
        assert msg.type == A2AMessageType.REQUEST
        assert msg.source_worker == "w1"
        assert msg.target_worker == "w2"
        assert msg.action == "ping"
        assert msg.payload == {}
        assert msg.correlation_id is not None
        assert msg.reply_to == ""
        assert msg.ttl_seconds == 30.0
        assert msg.trust_threshold == 0.0

    def test_to_dict(self):
        msg = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker="w1",
            target_worker="w2",
            action="ping",
            payload={"key": "val"},
            correlation_id="corr-123",
            reply_to="w1",
            trust_threshold=0.8,
        )
        d = msg.to_dict()
        assert d["type"] == "request"
        assert d["source_worker"] == "w1"
        assert d["target_worker"] == "w2"
        assert d["action"] == "ping"
        assert d["payload"] == {"key": "val"}
        assert d["correlation_id"] == "corr-123"
        assert d["reply_to"] == "w1"
        assert d["trust_threshold"] == 0.8

    def test_all_message_types(self):
        for mt in A2AMessageType:
            msg = A2AMessage(
                type=mt,
                source_worker="w1",
                target_worker="w2",
                action="act",
                payload={},
            )
            assert msg.to_dict()["type"] == mt.value


class TestA2AResponse:
    def test_defaults(self):
        resp = A2AResponse(correlation_id="corr-1", success=True, payload={"p": 1})
        assert resp.correlation_id == "corr-1"
        assert resp.success is True
        assert resp.payload == {"p": 1}
        assert resp.error == ""
        assert resp.source_worker == ""

    def test_to_dict(self):
        resp = A2AResponse(
            correlation_id="corr-1",
            success=True,
            payload={"p": 1},
            error="",
            source_worker="w2",
        )
        d = resp.to_dict()
        assert d["correlation_id"] == "corr-1"
        assert d["success"] is True
        assert d["payload"] == {"p": 1}
        assert d["source_worker"] == "w2"

    def test_error_response(self):
        resp = A2AResponse(
            correlation_id="corr-1",
            success=False,
            payload={},
            error="Something went wrong",
        )
        assert resp.success is False
        assert resp.error == "Something went wrong"


class TestA2AProtocol:
    @pytest.fixture
    def bus(self):
        b = AsyncMock()
        b.emit = AsyncMock(return_value=True)
        return b

    @pytest.fixture
    def protocol(self, bus):
        p = A2AProtocol(
            worker_id="w1",
            bus=bus,
            default_timeout=5.0,
            max_retries=2,
        )
        return p

    @pytest.mark.asyncio
    async def test_init(self, protocol):
        assert protocol.worker_id == "w1"
        assert protocol.message_count == 0
        assert protocol.failure_count == 0
        assert protocol.pending_count == 0
        assert protocol.handlers == {}

    @pytest.mark.asyncio
    async def test_register_handler(self, protocol):
        async def handler(payload):
            return {"ok": True}

        protocol.register_handler("ping", handler)
        assert "ping" in protocol.handlers

    @pytest.mark.asyncio
    async def test_unregister_handler(self, protocol):
        async def handler(payload):
            return {"ok": True}

        protocol.register_handler("ping", handler)
        protocol.unregister_handler("ping")
        assert "ping" not in protocol.handlers

    @pytest.mark.asyncio
    async def test_start_stop(self, protocol):
        await protocol.start()
        assert protocol._running is True
        assert protocol._consumer_task is not None
        await protocol.stop()
        assert protocol._running is False

    @pytest.mark.asyncio
    async def test_start_idempotent(self, protocol):
        await protocol.start()
        task = protocol._consumer_task
        await protocol.start()
        assert protocol._consumer_task is task

    @pytest.mark.asyncio
    async def test_send_message(self, protocol, bus):
        msg = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker="w1",
            target_worker="w2",
            action="ping",
            payload={},
        )
        ok = await protocol.send_message(msg)
        assert ok is True
        bus.emit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_no_bus(self):
        p = A2AProtocol(worker_id="w1")
        msg = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker="w1",
            target_worker="w2",
            action="ping",
            payload={},
        )
        ok = await p.send_message(msg)
        assert ok is False

    @pytest.mark.asyncio
    async def test_send_request_success(self, protocol, bus):
        async def handler(payload):
            return {"echo": payload.get("msg", "")}

        protocol.register_handler("echo", handler)

        async def respond():
            await asyncio.sleep(0.1)
            call_args = bus.emit.call_args
            emitted_payload = call_args[0][1]
            corr_id = emitted_payload["correlation_id"]
            response_payload = {
                "correlation_id": corr_id,
                "success": True,
                "payload": {"echo": "hello"},
                "error": "",
                "source_worker": "w2",
            }
            event = FakeEvent(
                "a2a.response",
                {
                    "target_worker": "w1",
                    "source_worker": "w2",
                    "type": "response",
                    "action": "echo",
                    "payload": response_payload,
                    "correlation_id": corr_id,
                },
            )
            protocol.handle_bus_event(event)

        result, _ = await asyncio.gather(
            protocol.send_request(
                target_worker="w2",
                action="echo",
                payload={"msg": "hello"},
            ),
            respond(),
        )
        assert result.success is True
        assert result.payload == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_send_request_timeout(self, protocol, bus):
        result = await protocol.send_request(
            target_worker="w2",
            action="no_handler",
            payload={},
            timeout=0.1,
        )
        assert result.success is False
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_send_request_send_failure(self, protocol):
        p = A2AProtocol(worker_id="w1")
        result = await p.send_request(
            target_worker="w2",
            action="ping",
            payload={},
        )
        assert result.success is False
        assert "Failed to send" in result.error

    @pytest.mark.asyncio
    async def test_send_response(self, protocol, bus):
        request = A2AMessage(
            type=A2AMessageType.REQUEST,
            source_worker="w2",
            target_worker="w1",
            action="ping",
            payload={},
            reply_to="w2",
            correlation_id="corr-1",
        )
        resp = A2AResponse(
            correlation_id="corr-1",
            success=True,
            payload={"pong": True},
        )
        ok = await protocol.send_response(request, resp)
        assert ok is True

    @pytest.mark.asyncio
    async def test_send_command(self, protocol, bus):
        ok = await protocol.send_command(
            target_worker="w2",
            action="reload",
            payload={"config": "new"},
        )
        assert ok is True

    @pytest.mark.asyncio
    async def test_broadcast(self, protocol, bus):
        sent = await protocol.broadcast(
            action="sync",
            payload={"data": 1},
            target_workers=["w2", "w3", "w4"],
        )
        assert sent == ["w2", "w3", "w4"]
        assert bus.emit.await_count == 3

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure(self, protocol):
        p = A2AProtocol(worker_id="w1")
        sent = await p.broadcast(
            action="sync",
            payload={},
            target_workers=["w2", "w3"],
        )
        assert sent == []

    @pytest.mark.asyncio
    async def test_handle_bus_event_non_a2a(self, protocol):
        event = FakeEvent("OTHER_EVENT", {})
        protocol.handle_bus_event(event)
        assert protocol.message_count == 0

    @pytest.mark.asyncio
    async def test_handle_bus_event_wrong_target(self, protocol):
        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w99",
                "source_worker": "w2",
                "type": "request",
                "action": "ping",
                "payload": {},
                "correlation_id": "c1",
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.message_count == 0

    @pytest.mark.asyncio
    async def test_handle_bus_event_no_source(self, protocol):
        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "type": "request",
                "action": "ping",
                "payload": {},
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.failure_count == 0
        assert protocol.message_count == 0

    @pytest.mark.asyncio
    async def test_handle_bus_event_unknown_type(self, protocol):
        event = FakeEvent(
            "a2a.unknown",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "unknown_type",
                "action": "ping",
                "payload": {},
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.failure_count == 1

    @pytest.mark.asyncio
    async def test_handle_bus_event_request(self, protocol):
        async def handler(payload):
            return {"echo": payload.get("msg", "")}

        protocol.register_handler("ping", handler)

        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "ping",
                "payload": {"msg": "hello"},
                "correlation_id": "c1",
                "reply_to": "w2",
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert protocol.message_count >= 1

    @pytest.mark.asyncio
    async def test_handle_bus_event_response(self, protocol, bus):
        event = FakeEvent(
            "a2a.response",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "response",
                "action": "echo",
                "payload": {
                    "correlation_id": "some-id",
                    "success": True,
                    "payload": {"echo": "hello"},
                    "error": "",
                    "source_worker": "w2",
                },
                "correlation_id": "some-id",
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.message_count == 1

    @pytest.mark.asyncio
    async def test_spiffe_rejects_unknown_worker(self, protocol):
        spiffe = MagicMock()
        spiffe.get_identity.return_value = None
        protocol._spiffe_manager = spiffe

        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "unknown",
                "type": "request",
                "action": "ping",
                "payload": {},
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.failure_count == 1

    @pytest.mark.asyncio
    async def test_trust_threshold_filter(self, protocol):
        trust = MagicMock()
        report = MagicMock()
        report.overall_score = 0.3
        trust.get_latest.return_value = report
        protocol._trust_scorer = trust

        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "ping",
                "payload": {},
                "trust_threshold": 0.7,
            },
        )
        protocol.handle_bus_event(event)
        assert protocol.failure_count == 1

    @pytest.mark.asyncio
    async def test_trust_threshold_passes(self, protocol, bus):
        trust = MagicMock()
        report = MagicMock()
        report.overall_score = 0.9
        trust.get_latest.return_value = report
        protocol._trust_scorer = trust

        async def handler(payload):
            return {"ok": True}

        protocol.register_handler("ping", handler)

        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "ping",
                "payload": {},
                "trust_threshold": 0.7,
                "reply_to": "",
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert protocol.message_count == 1
        assert protocol.failure_count == 0

    @pytest.mark.asyncio
    async def test_handle_request_no_handler(self, protocol, bus):
        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "no_handler",
                "payload": {},
                "correlation_id": "c1",
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert protocol.message_count == 1
        assert protocol.failure_count == 0

    @pytest.mark.asyncio
    async def test_handle_command(self, protocol, bus):
        results = []

        async def handler(payload):
            results.append(payload)

        protocol.register_handler("reload", handler)

        event = FakeEvent(
            "a2a.command",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "command",
                "action": "reload",
                "payload": {"cfg": "new"},
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert len(results) == 1
        assert results[0] == {"cfg": "new"}
        assert protocol.message_count == 1

    @pytest.mark.asyncio
    async def test_handle_command_no_handler(self, protocol, bus):
        event = FakeEvent(
            "a2a.command",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "command",
                "action": "no_handler",
                "payload": {},
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert protocol.message_count == 1

    @pytest.mark.asyncio
    async def test_handle_handler_error_sends_error_response(self, protocol, bus):
        async def handler(payload):
            raise ValueError("fail")

        protocol.register_handler("fail", handler)

        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "fail",
                "payload": {},
                "correlation_id": "c1",
                "reply_to": "w2",
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert bus.emit.await_count >= 1

    @pytest.mark.asyncio
    async def test_handle_bus_event_exception_safe(self, protocol):
        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
            },
        )
        protocol._spiffe_manager = MagicMock()
        protocol._spiffe_manager.get_identity.side_effect = RuntimeError("boom")
        protocol.handle_bus_event(event)
        assert protocol.failure_count == 1

    @pytest.mark.asyncio
    async def test_consume_loop_cleans_stale(self, protocol):
        protocol._running = True

        future = asyncio.get_event_loop().create_future()
        import time

        protocol._pending["stale-id"] = (future, time.time() - 10)
        protocol._consumer_task = asyncio.create_task(protocol._consume_loop())

        await asyncio.sleep(0.6)
        assert "stale-id" not in protocol._pending
        assert future.done()
        protocol._running = False
        if protocol._consumer_task:
            await asyncio.sleep(0.1)
            protocol._consumer_task.cancel()

    @pytest.mark.asyncio
    async def test_pending_count(self, protocol):
        protocol._pending["id1"] = (MagicMock(), 9999.0)
        assert protocol.pending_count == 1

    @pytest.mark.asyncio
    async def test_message_count_property(self, protocol):
        protocol._message_count = 5
        assert protocol.message_count == 5

    @pytest.mark.asyncio
    async def test_failure_count_property(self, protocol):
        protocol._failure_count = 3
        assert protocol.failure_count == 3

    @pytest.mark.asyncio
    async def test_handlers_property(self, protocol):
        async def h(p):
            return {}

        protocol.register_handler("test", h)
        assert isinstance(protocol.handlers, dict)
        assert "test" in protocol.handlers

    @pytest.mark.asyncio
    async def test_send_request_resolves_via_handle_response(self, protocol, bus):
        async def delayed_respond():
            await asyncio.sleep(0.1)
            call_args = bus.emit.call_args
            emitted_payload = call_args[0][1]
            corr_id = emitted_payload["correlation_id"]
            response_payload = {
                "correlation_id": corr_id,
                "success": True,
                "payload": {"echo": "done"},
                "error": "",
                "source_worker": "w2",
            }
            event = FakeEvent(
                "a2a.response",
                {
                    "target_worker": "w1",
                    "source_worker": "w2",
                    "type": "response",
                    "action": "echo",
                    "payload": response_payload,
                    "correlation_id": corr_id,
                },
            )
            protocol.handle_bus_event(event)

        result, _ = await asyncio.gather(
            protocol.send_request(
                target_worker="w2",
                action="echo",
                payload={"msg": "hello"},
                timeout=5.0,
            ),
            delayed_respond(),
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_handle_bus_event_with_data_not_dict(self, protocol):
        event = FakeEvent("a2a.request", "not a dict")
        protocol.handle_bus_event(event)
        assert protocol.message_count == 0
        assert protocol.failure_count == 0

    @pytest.mark.asyncio
    async def test_handle_bus_event_ttl_not_checked_on_receive(self, protocol):
        async def handler(p):
            return {"ok": True}

        protocol.register_handler("ping", handler)
        event = FakeEvent(
            "a2a.request",
            {
                "target_worker": "w1",
                "source_worker": "w2",
                "type": "request",
                "action": "ping",
                "payload": {},
                "correlation_id": "c1",
                "reply_to": "",
            },
        )
        protocol.handle_bus_event(event)
        await asyncio.sleep(0.05)
        assert protocol.message_count == 1

    @pytest.mark.asyncio
    async def test_stop_cancels_pending(self, protocol):
        future = asyncio.get_event_loop().create_future()
        import time

        protocol._pending["p1"] = (future, time.time() + 100)
        await protocol.stop()
        assert future.done()
        with pytest.raises(asyncio.TimeoutError):
            future.result()
