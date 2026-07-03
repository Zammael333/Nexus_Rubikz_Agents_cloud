import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ScoreFactor(Enum):
    CONSECUTIVE_FAILURES = "consecutive_failures"
    RECOVERY_COUNT = "recovery_count"
    BUDGET_CONSUMPTION = "budget_consumption"
    WATCHDOG_VIOLATIONS = "watchdog_violations"
    NEUTRALIZATION_ATTEMPTS = "neutralization_attempts"
    LATENCY_DEGRADATION = "latency_degradation"
    QUARANTINE_HISTORY = "quarantine_history"
    SCORPION_FINDINGS = "scorpion_findings"
    UPTIME = "uptime"


@dataclass
class ScoreReport:
    worker_id: str
    overall_score: float
    factors: dict[str, float]
    breakdown: dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "overall_score": self.overall_score,
            "factors": self.factors,
            "breakdown": self.breakdown,
            "timestamp": self.timestamp,
            "report_id": self.report_id,
        }


_WEIGHT_DEFAULTS: dict[ScoreFactor, float] = {
    ScoreFactor.CONSECUTIVE_FAILURES: 0.25,
    ScoreFactor.RECOVERY_COUNT: 0.10,
    ScoreFactor.BUDGET_CONSUMPTION: 0.20,
    ScoreFactor.WATCHDOG_VIOLATIONS: 0.15,
    ScoreFactor.NEUTRALIZATION_ATTEMPTS: 0.20,
    ScoreFactor.LATENCY_DEGRADATION: 0.05,
    ScoreFactor.QUARANTINE_HISTORY: 0.03,
    ScoreFactor.SCORPION_FINDINGS: 0.02,
    ScoreFactor.UPTIME: 0.00,
}


class TrustScorer:
    def __init__(self, weights: dict[ScoreFactor, float] | None = None):
        self._weights = weights or dict(_WEIGHT_DEFAULTS)
        self._score_history: dict[str, list[ScoreReport]] = {}
        logger.info("[TRUST_SCORE] Scorer initialized.")

    def compute(
        self,
        worker_id: str,
        consecutive_failures: int = 0,
        recovery_count: int = 0,
        budget_consumed: float = 0.0,
        watchdog_violations: int = 0,
        neutralization_attempts: int = 0,
        latency_p90_ms: float = 0.0,
        quarantine_count: int = 0,
        scorpion_findings: int = 0,
        uptime_hours: float = 0.0,
    ) -> ScoreReport:
        factor_scores: dict[str, float] = {}
        raw: dict[str, float] = {
            "consecutive_failures": max(0.0, 1.0 - (consecutive_failures / 10.0)),
            "recovery_count": max(0.0, 1.0 - (recovery_count / 50.0)),
            "budget_consumption": max(0.0, 1.0 - budget_consumed),
            "watchdog_violations": max(0.0, 1.0 - (watchdog_violations / 5.0)),
            "neutralization_attempts": max(0.0, 1.0 - (neutralization_attempts / 3.0)),
            "latency_degradation": max(0.0, 1.0 - (latency_p90_ms / 5000.0)),
            "quarantine_history": max(0.0, 1.0 - (quarantine_count / 5.0)),
            "scorpion_findings": max(0.0, 1.0 - (scorpion_findings / 10.0)),
            "uptime": min(1.0, uptime_hours / 720.0),
        }
        overall = 0.0
        for factor, weight in self._weights.items():
            score = raw.get(factor.value, 1.0)
            factor_scores[factor.value] = round(score, 4)
            overall += score * weight
        overall = round(max(0.0, min(1.0, overall)), 4)
        report = ScoreReport(
            worker_id=worker_id,
            overall_score=overall,
            factors=factor_scores,
            breakdown=raw,
        )
        if worker_id not in self._score_history:
            self._score_history[worker_id] = []
        self._score_history[worker_id].append(report)
        if len(self._score_history[worker_id]) > 100:
            self._score_history[worker_id] = self._score_history[worker_id][-100:]
        logger.info(
            f"[TRUST_SCORE] {worker_id}: {overall:.4f} "
            f"(failures={consecutive_failures}, budget={budget_consumed:.2f}, "
            f"neutralizations={neutralization_attempts})"
        )
        return report

    def get_history(self, worker_id: str, limit: int = 10) -> list[ScoreReport]:
        reports = self._score_history.get(worker_id, [])
        return reports[-limit:]

    def get_latest(self, worker_id: str) -> ScoreReport | None:
        history = self._score_history.get(worker_id, [])
        return history[-1] if history else None

    def interpret(self, score: float) -> str:
        if score >= 0.95:
            return "TRUSTED"
        elif score >= 0.85:
            return "RELIABLE"
        elif score >= 0.70:
            return "MONITOR"
        elif score >= 0.50:
            return "SUSPICIOUS"
        else:
            return "CONTAIN"

    def set_weight(self, factor: ScoreFactor, weight: float) -> None:
        self._weights[factor] = max(0.0, min(1.0, weight))

    def normalize_weights(self) -> None:
        total = sum(self._weights.values())
        if total > 0:
            for k in self._weights:
                self._weights[k] /= total
