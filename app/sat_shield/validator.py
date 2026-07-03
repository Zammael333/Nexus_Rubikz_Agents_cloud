from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.config import settings


@dataclass(frozen=True)
class SatShieldResult:
    platform_val: float
    ledger_val: float
    tax_factor: float
    discrepancy: float
    status: str
    verified: bool
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_val": self.platform_val,
            "ledger_val": self.ledger_val,
            "tax_factor": self.tax_factor,
            "da": self.discrepancy,
            "status": self.status,
            "verified": self.verified,
            "timestamp": self.timestamp,
        }




DA_THRESHOLD = settings.sat_shield_da_threshold


def calculate_da(
    platform_val: float, ledger_val: float, tax_factor: float
) -> SatShieldResult:
    discrepancy = abs(platform_val - ledger_val) + tax_factor
    verified = discrepancy < DA_THRESHOLD
    status = (
        "VERIFIED_COMPLIANT" if verified else "DISCREPANCY_DETECTED_ALERT_TRIGGERED"
    )
    return SatShieldResult(
        platform_val=round(platform_val, 4),
        ledger_val=round(ledger_val, 4),
        tax_factor=round(tax_factor, 4),
        discrepancy=round(discrepancy, 4),
        status=status,
        verified=verified,
        timestamp=datetime.now(UTC).isoformat(),
    )


def verify_ledger_consistency(
    entries: list[dict[str, float]], total: float, tolerance: float = DA_THRESHOLD
) -> bool:
    computed = sum(e.get("val", 0.0) for e in entries)
    return abs(computed - total) < tolerance
