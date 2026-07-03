import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_TWIN_FIDELITY_THRESHOLD = 0.001  # 0.1% max discrepancy


@dataclass
class FidelityReport:
    is_within_bounds: bool
    discrepancy_pct: float
    threshold_pct: float
    drifted_fields: list[dict[str, Any]]
    twin_snapshot: dict[str, Any] | None
    kernel_snapshot: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_within_bounds": self.is_within_bounds,
            "discrepancy_pct": self.discrepancy_pct,
            "threshold_pct": self.threshold_pct,
            "drifted_fields": self.drifted_fields,
            "timestamp": self.twin_snapshot.get("timestamp", "")
            if self.twin_snapshot
            else "",
        }


class TwinFidelityValidator:
    def __init__(self, emitter: Any, threshold: float = _TWIN_FIDELITY_THRESHOLD):
        self._emitter = emitter
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def validate(self) -> FidelityReport:
        all_snapshots = self._emitter.get_all_snapshots()
        max_drift = 0.0
        drifted_fields = []

        for worker_id, snap in all_snapshots.items():
            drift = self._emitter.get_drift(worker_id)
            max_drift = max(max_drift, drift)
            if drift > self._threshold:
                drifted_fields.append(
                    {
                        "provider": worker_id,
                        "drift": drift,
                        "fidelity": 1.0 - drift,
                        "status": snap.status,
                    }
                )

        discrepancy_pct = max_drift
        is_within = discrepancy_pct <= self._threshold

        twin_dict = (
            {wid: s.to_dict() for wid, s in all_snapshots.items()}
            if all_snapshots
            else None
        )

        return FidelityReport(
            is_within_bounds=is_within,
            discrepancy_pct=round(discrepancy_pct * 100, 6),
            threshold_pct=round(self._threshold * 100, 6),
            drifted_fields=drifted_fields,
            twin_snapshot=twin_dict,
            kernel_snapshot=(
                {"snapshot_count": len(all_snapshots)} if all_snapshots else None
            ),
        )

    def validate_emitter_drift(self) -> bool:
        all_snapshots = self._emitter.get_all_snapshots()
        if not all_snapshots:
            return False
        max_drift = max(
            (self._emitter.get_drift(wid) for wid in all_snapshots),
            default=0.0,
        )
        return max_drift <= self._threshold
