import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ReviewDecision(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass
class VibeDiffRecord:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    worker_id: str = ""
    action_type: str = ""
    action_payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    status: ReviewDecision = ReviewDecision.PENDING
    reviewer: str = ""
    reviewed_at: str = ""
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "worker_id": self.worker_id,
            "action_type": self.action_type,
            "action_payload": self.action_payload,
            "confidence": self.confidence,
            "status": self.status.value,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "reason": self.reason,
            "created_at": self.created_at,
        }


class VibeDiffDashboard:
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        on_review_callback: Callable[[VibeDiffRecord], None] | None = None,
        max_pending: int = 1000,
    ):
        self._threshold = confidence_threshold
        self._callback = on_review_callback
        self._max_pending = max_pending
        self._records: dict[str, VibeDiffRecord] = {}
        self._decided: dict[str, VibeDiffRecord] = {}

    def submit_decision(
        self,
        worker_id: str,
        action_type: str,
        action_payload: dict[str, Any],
        confidence: float,
        metadata: dict[str, Any] | None = None,
    ) -> VibeDiffRecord | None:
        if confidence >= self._threshold:
            return None
        if self.pending_count() >= self._max_pending:
            logger.warning(
                f"[VIBE_DIFF] Max pending reached ({self._max_pending}). Rejecting submission."
            )
            return None
        record = VibeDiffRecord(
            worker_id=worker_id,
            action_type=action_type,
            action_payload=action_payload,
            confidence=confidence,
            metadata=metadata or {},
        )
        self._records[record.decision_id] = record
        logger.info(
            f"[VIBE_DIFF] Decision {record.decision_id[:8]} submitted: "
            f"worker={worker_id} action={action_type} confidence={confidence:.2f}"
        )
        if self._callback:
            try:
                self._callback(record)
            except Exception as e:
                logger.error(f"[VIBE_DIFF] Callback failed: {e}")
        return record

    def review_decision(
        self,
        decision_id: str,
        decision: ReviewDecision,
        reviewer: str = "system",
        reason: str = "",
    ) -> bool:
        record = self._records.pop(decision_id, None)
        if record is None:
            logger.warning(f"[VIBE_DIFF] Decision {decision_id} not found.")
            return False
        record.status = decision
        record.reviewer = reviewer
        record.reviewed_at = datetime.now(UTC).isoformat()
        record.reason = reason
        self._decided[decision_id] = record
        logger.info(
            f"[VIBE_DIFF] Decision {decision_id[:8]} → {decision.value} by {reviewer}"
        )
        return True

    def get_pending(
        self, worker_id: str | None = None, action_type: str | None = None
    ) -> list[VibeDiffRecord]:
        records = list(self._records.values())
        if worker_id:
            records = [r for r in records if r.worker_id == worker_id]
        if action_type:
            records = [r for r in records if r.action_type == action_type]
        return sorted(records, key=lambda r: r.confidence)

    def get_decided(self, limit: int = 50) -> list[VibeDiffRecord]:
        records = list(self._decided.values())
        return sorted(records, key=lambda r: r.reviewed_at, reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        total_pending = len(self._records)
        total_decided = len(self._decided)
        approved = sum(
            1 for r in self._decided.values() if r.status == ReviewDecision.APPROVED
        )
        rejected = sum(
            1 for r in self._decided.values() if r.status == ReviewDecision.REJECTED
        )
        escalated = sum(
            1 for r in self._decided.values() if r.status == ReviewDecision.ESCALATED
        )
        return {
            "pending": total_pending,
            "decided": total_decided,
            "approved": approved,
            "rejected": rejected,
            "escalated": escalated,
            "threshold": self._threshold,
            "max_pending": self._max_pending,
        }

    def pending_count(self) -> int:
        return len(self._records)

    def auto_reject_expired(self, max_age_seconds: float = 86400) -> int:
        now = time.time()
        expired = []
        for did, record in list(self._records.items()):
            created = datetime.fromisoformat(record.created_at)
            age = now - created.timestamp()
            if age > max_age_seconds:
                record.status = ReviewDecision.REJECTED
                record.reviewer = "system"
                record.reviewed_at = datetime.now(UTC).isoformat()
                record.reason = "Auto-rejected: expired"
                self._decided[did] = record
                expired.append(did)
        for did in expired:
            self._records.pop(did, None)
        return len(expired)
