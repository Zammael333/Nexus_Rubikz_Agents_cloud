# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Edge Glow (Pasos 27, 48)
# Real-time system health indicator aggregating Phoenix, Budget, Bus, and SLO.

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Vinculante: SLO 99.9973%, Error Budget 0.0027%
_NOMINAL_SLO = settings.edge_glow_nominal_slo
_NOMINAL_ERROR_BUDGET = settings.edge_glow_nominal_error_budget


class SystemPulse(Enum):
    """Aggregate system health level."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


@dataclass(frozen=True)
class GlowSnapshot:
    """Immutable snapshot of the entire system health."""

    pulse: SystemPulse
    workers: dict[str, Any]
    budget: dict[str, Any]
    bus: dict[str, Any]
    scorpion_vectors: dict[str, str]
    slo: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pulse": self.pulse.value,
            "workers": self.workers,
            "budget": self.budget,
            "bus": self.bus,
            "scorpion_vectors": self.scorpion_vectors,
            "slo": dict(self.slo),
            "timestamp": self.timestamp,
        }


@dataclass
class SLOCalibrator:
    """Calibrates Edge Glow pulse based on real vs nominal SLO.

    Args:
        nominal_slo: Target SLO (default 0.999973 = 99.9973%).
        error_budget: Allowable error budget (default 0.000027 = 0.0027%).
    """

    nominal_slo: float = _NOMINAL_SLO
    error_budget: float = _NOMINAL_ERROR_BUDGET
    history: list[dict[str, Any]] = field(default_factory=list)

    def calibrate(
        self,
        real_slo: float,
        error_budget_remaining: float = 1.0,
        failures_last_hour: int = 0,
    ) -> dict[str, Any]:
        gap = self.nominal_slo - real_slo
        usage = 1.0 - error_budget_remaining

        if real_slo >= self.nominal_slo:
            slo_pulse = SystemPulse.GREEN
        elif usage >= 0.75:
            slo_pulse = SystemPulse.RED
        elif usage >= 0.5:
            slo_pulse = SystemPulse.ORANGE
        elif usage >= 0.25:
            slo_pulse = SystemPulse.YELLOW
        else:
            slo_pulse = SystemPulse.GREEN

        record = {
            "nominal_slo": self.nominal_slo,
            "real_slo": real_slo,
            "gap": gap,
            "error_budget_remaining": error_budget_remaining,
            "error_budget_usage_pct": round(usage * 100, 4),
            "failures_last_hour": failures_last_hour,
            "slo_pulse": slo_pulse.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.history.append(record)
        if len(self.history) > 1000:
            self.history = self.history[-500:]

        return record

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.history[-limit:]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nominal_slo": self.nominal_slo,
            "error_budget": self.error_budget,
            "history_size": len(self.history),
        }


class EdgeGlow:
    """Aggregates health data from Phoenix, Budget Watchdog, Bus, and SLO.

    Args:
        phoenix: PhoenixProtocol instance (optional).
        budget_watchdog: BudgetWatchdog instance (optional).
        bus_bridge: SyncBusBridge instance (optional).
        slo_calibrator: SLOCalibrator instance (optional).
    """

    def __init__(
        self,
        phoenix: Any = None,
        budget_watchdog: Any = None,
        bus_bridge: Any = None,
        slo_calibrator: SLOCalibrator | None = None,
    ):
        self._phoenix = phoenix
        self._budget = budget_watchdog
        self._bus = bus_bridge
        self._slo_calibrator = slo_calibrator or SLOCalibrator()

    def get_system_pulse(
        self,
        real_slo: float | None = None,
        error_budget_remaining: float = 1.0,
        failures_last_hour: int = 0,
    ) -> GlowSnapshot:
        workers_data = self._collect_workers()
        budget_data = self._collect_budget()
        bus_data = self._collect_bus()
        scorpion_data = self._collect_scorpion_status()

        slo_data = self._slo_calibrator.calibrate(
            real_slo=real_slo or self._estimate_slo(workers_data, bus_data),
            error_budget_remaining=error_budget_remaining,
            failures_last_hour=failures_last_hour,
        )

        pulse = self._compute_pulse(workers_data, budget_data, bus_data, slo_data)

        snapshot = GlowSnapshot(
            pulse=pulse,
            workers=workers_data,
            budget=budget_data,
            bus=bus_data,
            scorpion_vectors=scorpion_data,
            slo=slo_data,
            timestamp=datetime.now(UTC).isoformat(),
        )

        logger.info(f"[EDGE_GLOW] Pulse: {pulse.value}")
        return snapshot

    # -- Collectors ---------------------------------------------------------

    def _collect_workers(self) -> dict[str, Any]:
        if not self._phoenix:
            return {"status": "UNAVAILABLE", "workers": {}}

        reports = self._phoenix.get_all_reports()
        worker_data = {}
        for name, report in reports.items():
            worker_data[name] = {
                "status": report.status.value,
                "consecutive_failures": report.consecutive_failures,
                "recovery_count": report.recovery_count,
                "last_heartbeat": report.last_heartbeat,
                "recovery_epoch": report.recovery_epoch[:8] + "...",
            }

        statuses = [r.status.value for r in reports.values()]
        if "quarantined" in statuses:
            agg = "CRITICAL"
        elif "failed" in statuses:
            agg = "DEGRADED"
        elif "degraded" in statuses:
            agg = "WARNING"
        else:
            agg = "NOMINAL"

        return {
            "status": agg,
            "count": len(reports),
            "workers": worker_data,
        }

    def _collect_budget(self) -> dict[str, Any]:
        if not self._budget:
            return {"status": "UNAVAILABLE"}

        report = self._budget.check_budget()
        return report.to_dict()

    def _collect_bus(self) -> dict[str, Any]:
        if not self._bus:
            return {"status": "UNAVAILABLE"}

        return {
            "status": "OPERATIONAL",
            "event_count": self._bus.event_count,
            "queue_size": self._bus.queue_size,
            "dlq_size": self._bus.dlq_size,
            "recovery_epoch": self._bus.recovery_epoch[:8] + "...",
        }

    def _collect_scorpion_status(self) -> dict[str, str]:
        return {
            "SC-01_race_condition": "PARTIALLY_MITIGATED",
            "SC-02_accounting_drift": "MITIGATED",
            "SC-03_watchdog_fatigue": "PENDING",
            "SC-04_dead_letter_orphan": "MITIGATED",
            "SC-05_budget_exhaustion": "MITIGATED",
        }

    def _estimate_slo(self, workers: dict[str, Any], bus: dict[str, Any]) -> float:
        failures = 0
        total = 0
        for wdata in workers.get("workers", {}).values():
            total += 1
            if wdata.get("status") in ("failed", "quarantined", "degraded"):
                failures += 1
        event_count = bus.get("event_count", 1000)
        dlq = bus.get("dlq_size", 0)
        total_ops = max(total + event_count, 1)
        total_failures = failures + dlq
        estimated = 1.0 - (total_failures / total_ops)
        return max(0.0, estimated)

    @property
    def slo_calibrator(self) -> SLOCalibrator:
        return self._slo_calibrator

    # -- Pulse Computation --------------------------------------------------

    def _compute_pulse(
        self,
        workers: dict[str, Any],
        budget: dict[str, Any],
        bus: dict[str, Any],
        slo: dict[str, Any],
    ) -> SystemPulse:
        red_signals = 0
        yellow_signals = 0

        w_status = workers.get("status", "UNAVAILABLE")
        if w_status == "CRITICAL":
            red_signals += 1
        elif w_status in ("DEGRADED", "WARNING"):
            yellow_signals += 1

        b_status = budget.get("status", "UNAVAILABLE")
        if b_status == "frozen":
            red_signals += 1
        elif b_status == "warning":
            yellow_signals += 1

        dlq = bus.get("dlq_size", 0)
        if dlq > 100:
            red_signals += 1
        elif dlq > 10:
            yellow_signals += 1

        slo_pulse_str = slo.get("slo_pulse", "green")
        if slo_pulse_str == "red":
            red_signals += 1
        elif slo_pulse_str == "orange":
            yellow_signals += 2
        elif slo_pulse_str == "yellow":
            yellow_signals += 1

        if red_signals >= 2:
            return SystemPulse.RED
        elif red_signals == 1:
            return SystemPulse.ORANGE
        elif yellow_signals >= 2:
            return SystemPulse.ORANGE
        elif yellow_signals == 1:
            return SystemPulse.YELLOW
        else:
            return SystemPulse.GREEN
