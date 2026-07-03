from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrustAdaptiveLevel(Enum):
    ERROR = logging.ERROR
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG


_TRUST_TO_LEVEL: list[tuple[float, TrustAdaptiveLevel]] = [
    (0.0, TrustAdaptiveLevel.DEBUG),
    (0.3, TrustAdaptiveLevel.INFO),
    (0.6, TrustAdaptiveLevel.WARN),
    (0.9, TrustAdaptiveLevel.ERROR),
]


def trust_to_level(trust_score: float) -> TrustAdaptiveLevel:
    for threshold, level in reversed(_TRUST_TO_LEVEL):
        if trust_score >= threshold:
            return level
    return TrustAdaptiveLevel.DEBUG


@dataclass
class ProgressiveDisclosure:
    worker_id: str
    trust_score: float = 1.0
    _logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))
    _enabled: bool = True

    def update_trust(self, trust_score: float) -> None:
        self.trust_score = max(0.0, min(1.0, trust_score))

    @property
    def effective_level(self) -> int:
        return trust_to_level(self.trust_score).value

    def is_enabled_for(self, level: int) -> bool:
        if not self._enabled:
            return False
        return level >= self.effective_level

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.is_enabled_for(logging.DEBUG):
            self._logger.debug(f"[{self.worker_id}] {msg}", *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.is_enabled_for(logging.INFO):
            self._logger.info(f"[{self.worker_id}] {msg}", *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.is_enabled_for(logging.WARN):
            self._logger.warning(f"[{self.worker_id}] {msg}", *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.is_enabled_for(logging.ERROR):
            self._logger.error(f"[{self.worker_id}] {msg}", *args, **kwargs)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "trust_score": self.trust_score,
            "effective_level": logging.getLevelName(self.effective_level),
            "enabled": self._enabled,
        }
