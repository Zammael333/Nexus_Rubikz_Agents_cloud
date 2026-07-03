# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Reconciliation Worker Unit Tests (Paso 30)

import json

import pytest

from app.reconciliation_worker import run_periodic_reconciliation


class TestReconciliationWorker:
    """Tests for the Reconciliation Worker (Step 24)."""

    def test_all_entries_compliant(self):
        entries = [
            {
                "platform_val": 100.0,
                "ledger_val": 100.0,
                "tax_factor": 0.0,
                "val": 100.0,
            },
            {
                "platform_val": 200.0,
                "ledger_val": 200.0,
                "tax_factor": 0.0,
                "val": 200.0,
            },
        ]
        result = json.loads(
            run_periodic_reconciliation(json.dumps(entries), expected_total=300.0)
        )
        assert result["status"] == "RECONCILIATION_PASSED"
        assert result["summary"]["discrepancies_found"] == 0
        assert result["summary"]["ledger_consistency"] is True

    def test_discrepancy_detected(self):
        entries = [
            {"platform_val": 100.0, "ledger_val": 90.0, "tax_factor": 0.0, "val": 90.0},
        ]
        result = json.loads(
            run_periodic_reconciliation(json.dumps(entries), expected_total=90.0)
        )
        assert result["summary"]["discrepancies_found"] == 1
        assert (
            result["entry_results"][0]["status"]
            == "DISCREPANCY_DETECTED_ALERT_TRIGGERED"
        )

    def test_ledger_inconsistency(self):
        entries = [
            {
                "platform_val": 100.0,
                "ledger_val": 100.0,
                "tax_factor": 0.0,
                "val": 100.0,
            },
        ]
        result = json.loads(
            run_periodic_reconciliation(
                json.dumps(entries),
                expected_total=999.0,  # Wrong total
            )
        )
        assert result["summary"]["ledger_consistency"] is False
        assert "FAILURE" in result["status"]

    def test_critical_failure_both_issues(self):
        entries = [
            {"platform_val": 100.0, "ledger_val": 50.0, "tax_factor": 0.5, "val": 50.0},
        ]
        result = json.loads(
            run_periodic_reconciliation(json.dumps(entries), expected_total=999.0)
        )
        assert result["status"] == "RECONCILIATION_CRITICAL_FAILURE"
        assert result["summary"]["discrepancies_found"] == 1
        assert result["summary"]["ledger_consistency"] is False

    def test_empty_entries_error(self):
        result = json.loads(run_periodic_reconciliation("[]", expected_total=0.0))
        assert result["status"] == "ERROR"

    def test_invalid_json_error(self):
        result = json.loads(
            run_periodic_reconciliation("not valid json", expected_total=0.0)
        )
        assert result["status"] == "ERROR"
        assert "Invalid entries_json" in result["reason"]

    def test_multiple_entries_mixed(self):
        entries = [
            {
                "platform_val": 100.0,
                "ledger_val": 100.0,
                "tax_factor": 0.0,
                "val": 100.0,
            },
            {
                "platform_val": 200.0,
                "ledger_val": 150.0,
                "tax_factor": 0.5,
                "val": 150.0,
            },
            {
                "platform_val": 300.0,
                "ledger_val": 300.0,
                "tax_factor": 0.0,
                "val": 300.0,
            },
        ]
        result = json.loads(
            run_periodic_reconciliation(json.dumps(entries), expected_total=550.0)
        )
        assert result["summary"]["total_entries"] == 3
        assert result["summary"]["discrepancies_found"] == 1
        assert result["summary"]["entries_compliant"] == 2

    def test_average_da_computed(self):
        entries = [
            {
                "platform_val": 100.0,
                "ledger_val": 100.0,
                "tax_factor": 0.001,
                "val": 100.0,
            },
            {
                "platform_val": 100.0,
                "ledger_val": 100.0,
                "tax_factor": 0.003,
                "val": 100.0,
            },
        ]
        result = json.loads(
            run_periodic_reconciliation(json.dumps(entries), expected_total=200.0)
        )
        assert result["summary"]["average_da"] == pytest.approx(0.002, abs=1e-6)
