from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque

from dotenv import load_dotenv

from app.a2a.protocol import A2AProtocol
from app.a2a.transport import A2ATransport
from app.budget_watchdog import BudgetWatchdog
from app.config import settings
from app.dual_stability import DualStabilityMonitor
from app.edge_glow import EdgeGlow, SLOCalibrator
from app.otel import get_tracer, setup_telemetry
from app.otel.metrics import register_stability_gauges
from app.phoenix.protocol import PhoenixProtocol
from app.sat_shield.validator import calculate_da
from app.spiffe.manager import SpiffeManager
from app.twin.emitter import DigitalTwinEmitter
from app.twin.fidelity import TwinFidelityValidator

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

_spiffe = SpiffeManager()
_spiffe.register_all_workers()

_emitter = DigitalTwinEmitter(poll_interval=settings.twin_poll_interval)
_fidelity = TwinFidelityValidator(emitter=_emitter)

_a2a_protocol = A2AProtocol(worker_id="digital_twin", spiffe_manager=_spiffe)
_a2a_transport = A2ATransport(worker_id="digital_twin", spiffe_manager=_spiffe)

# Fidelity uses A2A protocol for drift broadcast on validation failures
_a2a_protocol.register_handler("fidelity_validate", _fidelity.validate)

_budget_watchdog = BudgetWatchdog(
    error_budget_percent=settings.error_budget_max_percent,
    window_seconds=settings.slo_window_hours * 3600,
)

_slo_calibrator = SLOCalibrator(
    nominal_slo=settings.edge_glow_nominal_slo,
    error_budget=settings.edge_glow_nominal_error_budget,
)

_phoenix = PhoenixProtocol()

_edge_glow = EdgeGlow(
    phoenix=_phoenix,
    budget_watchdog=_budget_watchdog,
    slo_calibrator=_slo_calibrator,
)

_stability_monitor = DualStabilityMonitor()

_da_history: deque[dict] = deque(maxlen=100)
_budget_history: deque[dict] = deque(maxlen=720)
_dag_graph: dict = {
    "nodes": [
        {"id": "kernel", "label": "Kernel", "type": "hub"},
        {"id": "twin", "label": "Digital Twin", "type": "twin"},
        {"id": "inventory", "label": "Inventory", "type": "worker"},
        {"id": "watchdog", "label": "Watchdog", "type": "worker"},
        {"id": "phoenix", "label": "Phoenix", "type": "worker"},
        {"id": "scorpion", "label": "Scorpion", "type": "scanner"},
        {"id": "sat-shield", "label": "SAT Shield", "type": "validator"},
        {"id": "notifier", "label": "Notifier", "type": "worker"},
        {"id": "budget", "label": "Budget Watcher", "type": "monitor"},
        {"id": "edge-glow", "label": "Edge Glow", "type": "monitor"},
        {"id": "sandbox", "label": "Sandbox", "type": "isolator"},
        {"id": "otel", "label": "OpenTelemetry", "type": "telemetry"},
    ],
    "edges": [
        {"source": "kernel", "target": "twin", "protocol": "a2a", "status": "active"},
        {"source": "kernel", "target": "inventory", "protocol": "internal", "status": "active"},
        {"source": "kernel", "target": "watchdog", "protocol": "internal", "status": "active"},
        {"source": "phoenix", "target": "kernel", "protocol": "health", "status": "active"},
        {"source": "phoenix", "target": "watchdog", "protocol": "health", "status": "active"},
        {"source": "phoenix", "target": "inventory", "protocol": "health", "status": "active"},
        {"source": "phoenix", "target": "scorpion", "protocol": "health", "status": "active"},
        {"source": "phoenix", "target": "sat-shield", "protocol": "health", "status": "active"},
        {"source": "phoenix", "target": "notifier", "protocol": "health", "status": "active"},
        {"source": "budget", "target": "kernel", "protocol": "slo", "status": "active"},
        {"source": "budget", "target": "phoenix", "protocol": "slo", "status": "active"},
        {"source": "edge-glow", "target": "budget", "protocol": "pulse", "status": "active"},
        {"source": "edge-glow", "target": "phoenix", "protocol": "pulse", "status": "active"},
        {"source": "edge-glow", "target": "kernel", "protocol": "pulse", "status": "active"},
        {"source": "scorpion", "target": "kernel", "protocol": "scan", "status": "active"},
        {"source": "sat-shield", "target": "kernel", "protocol": "da", "status": "active"},
        {"source": "notifier", "target": "kernel", "protocol": "alert", "status": "active"},
        {"source": "sandbox", "target": "kernel", "protocol": "isolate", "status": "active"},
        {"source": "otel", "target": "kernel", "protocol": "telemetry", "status": "active"},
        {"source": "otel", "target": "twin", "protocol": "telemetry", "status": "active"},
    ],
}


async def _record_budget_cycle():
    while True:
        try:
            report = _budget_watchdog.check_budget()
            _budget_history.append(report.to_dict())
        except Exception:
            logger.exception("budget cycle error")
        await asyncio.sleep(3600)


async def _record_pulse_cycle():
    while True:
        try:
            snapshot = _edge_glow.get_system_pulse(
                real_slo=100.0 - _budget_watchdog.check_budget().error_rate_percent / 100.0,
                error_budget_remaining=max(
                    0.0, 1.0 - _budget_watchdog.check_budget().budget_consumed_percent / 100.0
                ),
            )
            _stability_monitor.record(snapshot)
        except Exception:
            logger.exception("pulse cycle error")
        await asyncio.sleep(30)


async def _setup():
    await _a2a_protocol.start()
    await _a2a_transport.start_server(_a2a_protocol.handle_bus_event)


_background_tasks: list[asyncio.Task] = []


async def _lifespan(scope, receive, send):
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            setup_telemetry("nexus-rubykz-twin")
            register_stability_gauges(_stability_monitor)
            _background_tasks.append(asyncio.create_task(_setup()))
            _background_tasks.append(asyncio.create_task(_emitter.start()))
            _background_tasks.append(asyncio.create_task(_record_budget_cycle()))
            _background_tasks.append(asyncio.create_task(_record_pulse_cycle()))
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            for task in _background_tasks:
                task.cancel()
            await send({"type": "lifespan.shutdown.complete"})
            return


def _json_response(data) -> tuple[int, list[tuple], bytes]:
    body = json.dumps(data).encode()
    headers = [(b"content-type", b"application/json")]
    return 200, headers, body


_ROUTES: dict[str, tuple] = {}


async def _http_handler(scope, receive, send) -> int:
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        elif message["type"] == "http.disconnect":
            return 499

    path = scope["path"]
    status, headers, response_body = await _route(path)

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": response_body,
        }
    )
    return status


async def _route(path: str) -> tuple[int, list[tuple], bytes]:
    if path == "/healthz":
        return _json_response({"status": "ok", "role": "twin"})

    if path == "/readyz":
        fidelity = _fidelity.get_latest()
        ok = fidelity is None or fidelity.overall_score > 0.3
        status = 200 if ok else 503
        body = b'{"status":"ok","fidelity":true}' if ok else b'{"status":"degraded","fidelity":false}'
        return status, [(b"content-type", b"application/json")], body

    if path == "/startupz":
        return _json_response({"status": "ok", "phase": "bootstrap"})

    if path == "/api/v1/twin/snapshot":
        snapshot = _emitter.get_latest_snapshot()
        return _json_response(snapshot.to_dict() if snapshot else {})

    if path == "/api/v1/twin/fidelity":
        report = _fidelity.get_latest()
        return _json_response(report.to_dict() if report else {})

    if path == "/api/v1/twin/slo-metrics":
        report = _budget_watchdog.check_budget()
        slo_current = 100.0 - report.error_rate_percent
        return _json_response({
            "slo_target": settings.slo_target_percent,
            "slo_current": round(slo_current, 6),
            "error_budget_total": settings.error_budget_max_percent,
            "error_budget_remaining": round(
                max(0.0, settings.error_budget_max_percent - report.error_rate_percent), 6
            ),
            "total_requests": report.total_requests,
            "total_failures": report.total_failures,
            "error_rate_percent": report.error_rate_percent,
            "budget_consumed_percent": report.budget_consumed_percent,
            "allowed_failures_remaining": report.allowed_failures_remaining,
            "budget_status": report.status.value,
            "budget_history": list(_budget_history),
        })

    if path == "/api/v1/twin/budget-status":
        report = _budget_watchdog.check_budget()
        return _json_response({
            "report": report.to_dict(),
            "is_frozen": _budget_watchdog.is_frozen(),
            "warning_threshold": settings.watchdog_alert_threshold * 100.0,
            "freeze_threshold": settings.watchdog_freeze_threshold * 100.0,
            "window_hours": settings.slo_window_hours,
        })

    if path == "/api/v1/twin/sat-discrepancy":
        if _da_history:
            return _json_response({
                "entries": list(_da_history),
                "total_entries": len(_da_history),
            })
        result = calculate_da(platform_val=1000.0, ledger_val=999.5, tax_factor=0.002)
        return _json_response({
            "entries": [result.to_dict()],
            "total_entries": 1,
        })

    if path == "/api/v1/twin/phoenix-reports":
        reports = _phoenix.get_all_reports()
        report_dict = {}
        for name, r in reports.items():
            report_dict[name] = {
                "worker_id": r.worker_id,
                "status": r.status.value,
                "latency_ms": r.latency_ms,
                "last_heartbeat": r.last_heartbeat,
                "consecutive_failures": r.consecutive_failures,
                "recovery_count": r.recovery_count,
                "recovery_epoch": r.recovery_epoch,
            }
        return _json_response({
            "workers": report_dict,
            "total_workers": len(report_dict),
        })

    if path == "/api/v1/twin/stability-tensor":
        return _json_response(_stability_monitor.evaluate().to_dict())

    if path == "/api/v1/twin/edge-glow":
        snapshot = _edge_glow.get_system_pulse(
            real_slo=100.0 - _budget_watchdog.check_budget().error_rate_percent / 100.0,
            error_budget_remaining=max(
                0.0, 1.0 - _budget_watchdog.check_budget().budget_consumed_percent / 100.0
            ),
        )
        return _json_response(snapshot.to_dict())

    if path == "/api/v1/twin/dag-graph":
        frozen = _budget_watchdog.is_frozen()
        dag = {
            "nodes": _dag_graph["nodes"],
            "edges": [
                {**e, "status": "frozen" if frozen else e["status"]}
                for e in _dag_graph["edges"]
            ],
            "metadata": {
                "pulse": _edge_glow.get_system_pulse().pulse.value if frozen else "green",
                "is_frozen": frozen,
            },
        }
        return _json_response(dag)

    return 404, [(b"content-type", b"application/json")], b'{"error":"not_found"}'


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        await _lifespan(scope, receive, send)
        return

    method = scope.get("method", "UNKNOWN")
    path = scope.get("path", "/")
    tracer = get_tracer("twin.http")

    with tracer.start_as_current_span(
        f"{method} {path}",
        attributes={
            "http.method": method,
            "http.url": path,
            "http.scheme": scope.get("scheme", "http"),
        },
        record_exception=True,
    ) as span:
        start = time.monotonic()
        status = await _http_handler(scope, receive, send)
        elapsed = time.monotonic() - start
        span.set_attribute("http.status_code", status)
        span.set_attribute("http.duration_ms", round(elapsed * 1000, 2))
