from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.edge_glow import GlowSnapshot, SystemPulse

logger = logging.getLogger(__name__)

PULSE_RANK = {
    SystemPulse.GREEN: 0,
    SystemPulse.YELLOW: 1,
    SystemPulse.ORANGE: 2,
    SystemPulse.RED: 3,
}


class StabilityClass(Enum):
    CONVERGENT = "convergent"
    DIVERGENT = "divergent"
    OSCILLATING = "oscillating"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class StabilityTensor:
    classification: StabilityClass
    current_pulse: str
    prior_pulse: str | None
    window_size: int
    samples_in_window: int
    pulse_transitions: int
    trend_slope: float
    mean_pulse_rank: float
    std_pulse_rank: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "current_pulse": self.current_pulse,
            "prior_pulse": self.prior_pulse,
            "window_size_seconds": self.window_size,
            "samples_in_window": self.samples_in_window,
            "pulse_transitions": self.pulse_transitions,
            "trend_slope": round(self.trend_slope, 4),
            "mean_pulse_rank": round(self.mean_pulse_rank, 4),
            "std_pulse_rank": round(self.std_pulse_rank, 4),
            "timestamp": self.timestamp,
        }


class DualStabilityMonitor:
    """Monitors EdgeGlow pulse history to detect convergence/divergence/oscillation.

    Maintains a sliding window of GlowSnapshots and computes a StabilityTensor
    on demand, classifying the system's short-term stability trajectory.

    Args:
        window_seconds: Sliding time window (default 300 = 5 min).
        max_samples: Max snapshots retained (default 500).
    """

    def __init__(
        self,
        window_seconds: int = 300,
        max_samples: int = 500,
    ):
        self._window_seconds = window_seconds
        self._history: deque[GlowSnapshot] = deque(maxlen=max_samples)

    def record(self, snapshot: GlowSnapshot) -> None:
        self._history.append(snapshot)

    def evaluate(self) -> StabilityTensor:
        now = datetime.now(UTC)
        cutoff = now.timestamp() - self._window_seconds
        filtered = [s for s in self._history if _snapshot_ts(s) >= cutoff]

        if len(filtered) < 2:
            return StabilityTensor(
                classification=StabilityClass.INSUFFICIENT_DATA,
                current_pulse=filtered[-1].pulse.value if filtered else "unknown",
                prior_pulse=None,
                window_size=self._window_seconds,
                samples_in_window=len(filtered),
                pulse_transitions=0,
                trend_slope=0.0,
                mean_pulse_rank=0.0,
                std_pulse_rank=0.0,
                timestamp=now.isoformat(),
            )

        ranks = [PULSE_RANK[s.pulse] for s in filtered]
        current = filtered[-1].pulse
        prior = filtered[0].pulse

        transitions = sum(1 for i in range(1, len(ranks)) if ranks[i] != ranks[i - 1])
        mean_r = sum(ranks) / len(ranks)
        variance = sum((r - mean_r) ** 2 for r in ranks) / len(ranks)
        std_r = variance ** 0.5

        # linear regression slope via least-squares
        n = len(ranks)
        xs = list(range(n))
        sx = sum(xs)
        sy = sum(ranks)
        sxx = sum(x * x for x in xs)
        sxy = sum(x * r for x, r in zip(xs, ranks, strict=True))
        denom = n * sxx - sx * sx
        slope = (n * sxy - sx * sy) / denom if denom else 0.0

        # classify
        if abs(slope) < 0.01 and transitions < 2:
            classification = StabilityClass.STABLE
        elif slope < -0.01 and all(
            PULSE_RANK[filtered[i].pulse] <= PULSE_RANK[filtered[i - 1].pulse]
            for i in range(1, len(filtered))
        ):
            classification = StabilityClass.CONVERGENT
        elif slope > 0.01 and all(
            PULSE_RANK[filtered[i].pulse] >= PULSE_RANK[filtered[i - 1].pulse]
            for i in range(1, len(filtered))
        ):
            classification = StabilityClass.DIVERGENT
        else:
            classification = StabilityClass.OSCILLATING

        return StabilityTensor(
            classification=classification,
            current_pulse=current.value,
            prior_pulse=prior.value,
            window_size=self._window_seconds,
            samples_in_window=len(filtered),
            pulse_transitions=transitions,
            trend_slope=slope,
            mean_pulse_rank=mean_r,
            std_pulse_rank=std_r,
            timestamp=now.isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_seconds": self._window_seconds,
            "history_length": len(self._history),
        }


def _snapshot_ts(snapshot: GlowSnapshot) -> float:
    try:
        return datetime.fromisoformat(snapshot.timestamp).timestamp()
    except (ValueError, TypeError):
        return 0.0
