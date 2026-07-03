from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry.metrics import CallbackOptions, Observation

from app.otel import get_meter

if TYPE_CHECKING:
    from app.dual_stability import DualStabilityMonitor

logger = logging.getLogger(__name__)

_METER_NAME = "nexus-rubykz.stability"


def register_stability_gauges(
    monitor: DualStabilityMonitor,
) -> None:
    """Register ObservableGauge instruments fed by the DualStabilityMonitor.

    All callbacks are synchronous microsecond-reads of in-memory state; the
    PeriodicExportingMetricReader handles OTLP export in a background thread
    without blocking the application hot path.
    """
    meter = get_meter(_METER_NAME)

    def _slope_cb(_options: CallbackOptions):
        tensor = monitor.evaluate()
        yield Observation(
            value=tensor.trend_slope,
            attributes={
                "classification": tensor.classification.value,
                "current_pulse": tensor.current_pulse,
            },
        )

    def _transitions_cb(_options: CallbackOptions):
        tensor = monitor.evaluate()
        yield Observation(
            value=tensor.pulse_transitions,
            attributes={
                "classification": tensor.classification.value,
                "samples": str(tensor.samples_in_window),
            },
        )

    def _rank_cb(_options: CallbackOptions):
        tensor = monitor.evaluate()
        yield Observation(
            value=tensor.mean_pulse_rank,
            attributes={
                "classification": tensor.classification.value,
                "std_dev": str(round(tensor.std_pulse_rank, 4)),
            },
        )

    def _stability_class_cb(_options: CallbackOptions):
        tensor = monitor.evaluate()
        for _idx, label in enumerate(
            ["convergent", "divergent", "oscillating", "stable", "insufficient_data"]
        ):
            yield Observation(
                value=1.0 if tensor.classification.value == label else 0.0,
                attributes={"stability_class": label},
            )

    meter.create_observable_gauge(
        name="stability.trend_slope",
        callbacks=[_slope_cb],
        description="Linear-regression slope of pulse-rank history (negative = convergent)",
        unit="1",
    )

    meter.create_observable_gauge(
        name="stability.pulse_transitions",
        callbacks=[_transitions_cb],
        description="Number of pulse transitions in the current sliding window",
        unit="1",
    )

    meter.create_observable_gauge(
        name="stability.mean_pulse_rank",
        callbacks=[_rank_cb],
        description="Mean pulse rank in the current window (0=GREEN ... 3=RED)",
        unit="1",
    )

    meter.create_observable_gauge(
        name="stability.classification",
        callbacks=[_stability_class_cb],
        description="One-hot encoding of the current StabilityClass",
        unit="1",
    )

    logger.info(
        "[OTEL] Stability gauges registered -- meter=%s instruments=4",
        _METER_NAME,
    )
