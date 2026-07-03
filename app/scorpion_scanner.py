# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Scorpion Inventory Scanner (Paso 26)
# Forensic analysis of inventory locks to detect race conditions,
# dead stock, and double allocation.

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Detection thresholds
RACE_CONDITION_WINDOW_SECONDS = settings.scorpion_race_window_seconds
DEAD_STOCK_DAYS = settings.scorpion_dead_stock_days


def scorpion_inventory_scan(sku: str, vault: Any = None) -> str:
    """Performs a Scorpion forensic scan on an inventory SKU.

    Detects:
      - Race conditions: Multiple locks on the same SKU within a 1s window.
      - Dead stock: SKUs with no movement in 30+ days.
      - Double allocation: Duplicate tx_tokens in the transaction log.

    Args:
        sku: The SKU identifier to scan.
        vault: NexusVault instance for database queries. If None, returns
            a skeleton report indicating vault is unavailable.

    Returns:
        JSON string with scan results for each threat vector.
    """
    findings: list[dict[str, Any]] = []
    severity = "CLEAN"

    if vault is None:
        return json.dumps(
            {
                "sku": sku,
                "status": "SCAN_SKIPPED",
                "reason": "NexusVault not available. Cannot perform forensic scan.",
                "findings": [],
            }
        )

    # --- Vector SC-01: Race Condition Detection ---
    try:
        recent_locks = vault.get_locks_in_window(sku, RACE_CONDITION_WINDOW_SECONDS)
        if len(recent_locks) > 1:
            findings.append(
                {
                    "vector": "SC-01",
                    "threat": "RACE_CONDITION",
                    "severity": "CRITICAL",
                    "detail": (
                        f"{len(recent_locks)} locks detected on SKU '{sku}' "
                        f"within {RACE_CONDITION_WINDOW_SECONDS}s window"
                    ),
                    "locks": [lock.to_dict() for lock in recent_locks],
                }
            )
            severity = "CRITICAL"
    except Exception as e:
        findings.append(
            {
                "vector": "SC-01",
                "threat": "RACE_CONDITION",
                "severity": "ERROR",
                "detail": f"Scan error: {e}",
            }
        )

    # --- Dead Stock Detection ---
    try:
        all_locks = vault.get_locks_for_sku(sku)
        if all_locks:
            most_recent = all_locks[0]  # sorted DESC by created_at
            try:
                last_activity = datetime.fromisoformat(most_recent.created_at)
                now = datetime.now(UTC)
                days_idle = (now - last_activity).days
                if days_idle >= DEAD_STOCK_DAYS:
                    findings.append(
                        {
                            "vector": "DEAD_STOCK",
                            "threat": "DEAD_STOCK",
                            "severity": "MEDIUM",
                            "detail": (
                                f"SKU '{sku}' has been idle for {days_idle} days "
                                f"(threshold: {DEAD_STOCK_DAYS}d)"
                            ),
                            "last_activity": most_recent.created_at,
                        }
                    )
                    if severity != "CRITICAL":
                        severity = "MEDIUM"
            except (ValueError, TypeError):
                pass  # Malformed timestamp, skip
        else:
            findings.append(
                {
                    "vector": "DEAD_STOCK",
                    "threat": "NO_HISTORY",
                    "severity": "LOW",
                    "detail": f"No lock history found for SKU '{sku}'",
                }
            )
    except Exception as e:
        findings.append(
            {
                "vector": "DEAD_STOCK",
                "threat": "DEAD_STOCK",
                "severity": "ERROR",
                "detail": f"Scan error: {e}",
            }
        )

    # --- Double Allocation Detection ---
    try:
        duplicate_tokens = vault.find_duplicate_tokens()
        # Filter: check if any duplicate tokens relate to our SKU
        sku_locks = vault.get_locks_for_sku(sku)
        sku_tokens = {lock.tx_token for lock in sku_locks}
        sku_duplicates = sku_tokens & set(duplicate_tokens)

        if sku_duplicates:
            findings.append(
                {
                    "vector": "DOUBLE_ALLOCATION",
                    "threat": "DOUBLE_ALLOCATION",
                    "severity": "CRITICAL",
                    "detail": (
                        f"{len(sku_duplicates)} duplicate tx_tokens found "
                        f"for SKU '{sku}'"
                    ),
                    "duplicate_tokens": list(sku_duplicates),
                }
            )
            severity = "CRITICAL"
    except Exception as e:
        findings.append(
            {
                "vector": "DOUBLE_ALLOCATION",
                "threat": "DOUBLE_ALLOCATION",
                "severity": "ERROR",
                "detail": f"Scan error: {e}",
            }
        )

    scan_status = "CLEAN" if not findings or severity == "LOW" else "THREATS_DETECTED"

    report = {
        "sku": sku,
        "status": scan_status,
        "severity": severity,
        "findings_count": len(findings),
        "findings": findings,
        "scanned_at": datetime.now(UTC).isoformat(),
    }

    logger.info(
        f"[SCORPION] SKU '{sku}': {scan_status} "
        f"(severity={severity}, findings={len(findings)})"
    )

    return json.dumps(report, ensure_ascii=False)
