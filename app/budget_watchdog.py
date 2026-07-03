# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Budget Watchdog (Paso 23)
# Monitoreo de Error Budget en tiempo real con ventana deslizante.
# Scorpion SC-05 mitigation.

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.config import settings
from app.otel.injector import OtelInjector

_otel = OtelInjector("nexus-rubykz-budget")
_budget_count = _otel.counter("budget.requests.total", "Total requests recorded by BudgetWatchdog")
_budget_failures = _otel.counter("budget.failures.total", "Total failures recorded by BudgetWatchdog")

logger = logging.getLogger(__name__)

# Default: 0.027% error budget over a 30-day window
DEFAULT_ERROR_BUDGET_PERCENT = settings.error_budget_max_percent
DEFAULT_WINDOW_SECONDS = settings.slo_window_hours * 3600  # convert hours to seconds
WARNING_THRESHOLD_PERCENT = settings.watchdog_alert_threshold * 100.0
FREEZE_THRESHOLD_PERCENT = settings.watchdog_freeze_threshold * 100.0


class BudgetStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    FROZEN = "frozen"


@dataclass(frozen=True)
class BudgetReport:
    """Immutable snapshot of the current error budget state."""

    total_requests: int
    total_failures: int
    error_rate_percent: float
    budget_consumed_percent: float
    status: BudgetStatus
    allowed_failures_remaining: int
    window_seconds: float
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "error_rate_percent": round(self.error_rate_percent, 6),
            "budget_consumed_percent": round(self.budget_consumed_percent, 2),
            "status": self.status.value,
            "allowed_failures_remaining": self.allowed_failures_remaining,
            "window_seconds": self.window_seconds,
            "timestamp": self.timestamp,
        }


class BudgetWatchdog:
    """Monitors the SLO error budget in real-time using a sliding window.

    Records every success/failure and computes:
      error_rate = failures / total_requests
      budget_consumed = (error_rate / error_budget) * 100

    Thresholds:
      - 50% consumed → WARNING (emit BUDGET_WARNING event)
      - 100% consumed → FROZEN (emit BUDGET_EXHAUSTED event, reject operations)

    Thread-safe: uses a lock for all counter mutations.

    Args:
        error_budget_percent: Maximum allowed error rate (default 0.027%).
        window_seconds: Sliding window in seconds (default 30 days).
        on_warning: Optional callback(report) when budget hits 50%.
        on_freeze: Optional callback(report) when budget hits 100%.
    """

    def __init__(
        self,
        error_budget_percent: float = DEFAULT_ERROR_BUDGET_PERCENT,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        on_warning: Any = None,
        on_freeze: Any = None,
    ):
        self._budget_percent = error_budget_percent
        self._window_seconds = window_seconds
        self._on_warning = on_warning
        self._on_freeze = on_freeze

        # Sliding window: list of (timestamp, is_failure: bool)
        self._records: list[tuple[float, bool]] = []
        self._lock = threading.Lock()
        self._was_warning = False
        self._was_frozen = False

    # -- Recording ----------------------------------------------------------

    def record_success(self) -> BudgetReport:
        """Record a successful request and return the updated budget report."""
        return self._record(is_failure=False)

    def record_failure(self) -> BudgetReport:
        """Record a failed request and return the updated budget report."""
        return self._record(is_failure=True)

    def _record(self, is_failure: bool) -> BudgetReport:
        now = time.time()
        with self._lock:
            self._records.append((now, is_failure))
            self._prune(now)
            report = self._compute_report(now)

        _budget_count.add(1, {"status": report.status.value})
        if is_failure:
            _budget_failures.add(1, {"status": report.status.value})

        # Trigger callbacks on state transitions
        if report.status == BudgetStatus.WARNING and not self._was_warning:
            self._was_warning = True
            logger.warning(
                f"[BUDGET_WATCHDOG] WARNING: Error budget at "
                f"{report.budget_consumed_percent:.1f}% "
                f"({report.total_failures} failures / {report.total_requests} total)"
            )
            if self._on_warning:
                self._on_warning(report)

        if report.status == BudgetStatus.FROZEN and not self._was_frozen:
            self._was_frozen = True
            logger.critical(
                f"[BUDGET_WATCHDOG] FROZEN: Error budget EXHAUSTED at "
                f"{report.budget_consumed_percent:.1f}%. "
                f"Deploy freeze enforced."
            )
            if self._on_freeze:
                self._on_freeze(report)

        # Reset flags if we recover
        if report.status == BudgetStatus.HEALTHY:
            self._was_warning = False
            self._was_frozen = False

        return report

    # -- Query --------------------------------------------------------------

    def check_budget(self) -> BudgetReport:
        """Return the current budget report without recording an event."""
        now = time.time()
        with self._lock:
            self._prune(now)
            return self._compute_report(now)

    def is_frozen(self) -> bool:
        """Quick check: is the system currently frozen?"""
        return self.check_budget().status == BudgetStatus.FROZEN

    def reset(self) -> None:
        """Reset all counters (new budget cycle)."""
        with self._lock:
            self._records.clear()
            self._was_warning = False
            self._was_frozen = False
        logger.info("[BUDGET_WATCHDOG] Budget reset. New cycle started.")

    # -- Internals ----------------------------------------------------------

    def _prune(self, now: float) -> None:
        """Remove records outside the sliding window. Must hold _lock."""
        cutoff = now - self._window_seconds
        self._records = [(ts, fail) for ts, fail in self._records if ts >= cutoff]

    def _compute_report(self, now: float) -> BudgetReport:
        """Compute the budget report from current records. Must hold _lock."""
        total = len(self._records)
        failures = sum(1 for _, fail in self._records if fail)

        if total == 0:
            return BudgetReport(
                total_requests=0,
                total_failures=0,
                error_rate_percent=0.0,
                budget_consumed_percent=0.0,
                status=BudgetStatus.HEALTHY,
                allowed_failures_remaining=0,
                window_seconds=self._window_seconds,
                timestamp=now,
            )

        error_rate = (failures / total) * 100  # as percentage
        budget_consumed = (error_rate / self._budget_percent) * 100

        if budget_consumed >= FREEZE_THRESHOLD_PERCENT:
            status = BudgetStatus.FROZEN
        elif budget_consumed >= WARNING_THRESHOLD_PERCENT:
            status = BudgetStatus.WARNING
        else:
            status = BudgetStatus.HEALTHY

        # How many more failures can we tolerate?
        max_allowed = (self._budget_percent / 100) * total
        remaining = max(0, int(max_allowed - failures))

        return BudgetReport(
            total_requests=total,
            total_failures=failures,
            error_rate_percent=error_rate,
            budget_consumed_percent=min(budget_consumed, 999.99),
            status=status,
            allowed_failures_remaining=remaining,
            window_seconds=self._window_seconds,
            timestamp=now,
        )
