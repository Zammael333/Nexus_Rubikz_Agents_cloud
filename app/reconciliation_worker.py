# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Reconciliation Worker (Paso 24)
# Periodic accounting reconciliation using SAT Shield edge validation.

import json
import logging
from typing import Any

from app.sat_shield.validator import calculate_da, verify_ledger_consistency

logger = logging.getLogger(__name__)


def run_periodic_reconciliation(entries_json: str, expected_total: float) -> str:
    """Executes periodic accounting reconciliation using SAT Shield validators.

    Processes a batch of ledger entries, validates each against the Da equation,
    and performs a cross-check of the total against the expected value.

    Args:
        entries_json: JSON string of ledger entries. Each entry must have
            'platform_val', 'ledger_val', 'tax_factor', and optionally 'val'
            for the consistency check. Example:
            '[{"platform_val": 100.0, "ledger_val": 100.0, "tax_factor": 0.0, "val": 100.0}]'
        expected_total: The expected grand total of all entry values for
            cross-validation via verify_ledger_consistency().

    Returns:
        JSON string with reconciliation results including per-entry Da status,
        overall consistency check, and summary statistics.
    """
    try:
        entries: list[dict[str, Any]] = json.loads(entries_json)
    except (json.JSONDecodeError, TypeError) as e:
        return json.dumps(
            {
                "status": "ERROR",
                "reason": f"Invalid entries_json: {e}",
            }
        )

    if not entries:
        return json.dumps(
            {
                "status": "ERROR",
                "reason": "No entries provided for reconciliation.",
            }
        )

    # Phase 1: Per-entry Da validation
    entry_results = []
    discrepancies_found = 0
    total_da = 0.0

    for i, entry in enumerate(entries):
        platform_val = entry.get("platform_val", 0.0)
        ledger_val = entry.get("ledger_val", 0.0)
        tax_factor = entry.get("tax_factor", 0.0)

        result = calculate_da(platform_val, ledger_val, tax_factor)
        total_da += result.discrepancy

        if not result.verified:
            discrepancies_found += 1

        entry_results.append(
            {
                "entry_index": i,
                "da": result.discrepancy,
                "status": result.status,
                "verified": result.verified,
                "platform_val": result.platform_val,
                "ledger_val": result.ledger_val,
                "tax_factor": result.tax_factor,
            }
        )

    # Phase 2: Ledger consistency cross-check
    consistency_entries = [
        {"val": e.get("val", e.get("ledger_val", 0.0))} for e in entries
    ]
    ledger_consistent = verify_ledger_consistency(consistency_entries, expected_total)

    # Phase 3: Summary
    total_entries = len(entries)
    avg_da = total_da / total_entries if total_entries > 0 else 0.0

    if discrepancies_found == 0 and ledger_consistent:
        overall_status = "RECONCILIATION_PASSED"
    elif discrepancies_found > 0 and not ledger_consistent:
        overall_status = "RECONCILIATION_CRITICAL_FAILURE"
    else:
        overall_status = "RECONCILIATION_PARTIAL_FAILURE"

    report = {
        "status": overall_status,
        "summary": {
            "total_entries": total_entries,
            "discrepancies_found": discrepancies_found,
            "entries_compliant": total_entries - discrepancies_found,
            "average_da": round(avg_da, 6),
            "total_da": round(total_da, 6),
            "ledger_consistency": ledger_consistent,
            "expected_total": expected_total,
        },
        "entry_results": entry_results,
    }

    logger.info(
        f"[RECONCILIATION] {overall_status}: "
        f"{total_entries - discrepancies_found}/{total_entries} compliant, "
        f"avg Da={avg_da:.6f}, ledger_consistent={ledger_consistent}"
    )

    return json.dumps(report, ensure_ascii=False)
