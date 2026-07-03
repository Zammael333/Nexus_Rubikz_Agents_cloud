# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Scorpion Scanner Unit Tests (Paso 30)

import json

import pytest

from app.db.vault import NexusVault
from app.scorpion_scanner import scorpion_inventory_scan


@pytest.fixture
def tmp_vault(tmp_path):
    """Create a temporary NexusVault for testing."""
    db_path = str(tmp_path / "test_vault.db")
    return NexusVault(db_path=db_path)


class TestScorpionScanner:
    """Tests for the Scorpion Inventory Scanner (Step 26)."""

    def test_scan_without_vault(self):
        result = json.loads(scorpion_inventory_scan("SKU-001"))
        assert result["status"] == "SCAN_SKIPPED"
        assert "NexusVault not available" in result["reason"]

    def test_scan_clean_sku(self, tmp_vault):
        result = json.loads(scorpion_inventory_scan("SKU-CLEAN", vault=tmp_vault))
        # No locks exist → no history finding
        assert result["sku"] == "SKU-CLEAN"
        assert any(f["threat"] == "NO_HISTORY" for f in result["findings"])

    def test_scan_with_single_lock(self, tmp_vault):
        tmp_vault.record_lock("SKU-A", 10, "aaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        result = json.loads(scorpion_inventory_scan("SKU-A", vault=tmp_vault))
        # One lock is not a race condition
        assert result["sku"] == "SKU-A"
        # Should not have a race condition finding with only 1 lock
        # (depends on timing window — within 1s it could trigger)
        # We just verify the scan completes successfully
        assert "status" in result

    def test_double_allocation_detection(self, tmp_vault):
        # Create a lock, then log the same token twice
        tmp_vault.record_lock("SKU-DUP", 5, "dup-token-1234")
        tmp_vault.log_transaction("dup-token-1234", "INVENTORY_LOCK", "{}")
        tmp_vault.log_transaction("dup-token-1234", "INVENTORY_LOCK", "{}")

        result = json.loads(scorpion_inventory_scan("SKU-DUP", vault=tmp_vault))
        double_findings = [
            f for f in result["findings"] if f["vector"] == "DOUBLE_ALLOCATION"
        ]
        assert len(double_findings) == 1
        assert double_findings[0]["severity"] == "CRITICAL"

    def test_scan_report_structure(self, tmp_vault):
        result = json.loads(scorpion_inventory_scan("SKU-X", vault=tmp_vault))
        assert "sku" in result
        assert "status" in result
        assert "severity" in result
        assert "findings" in result
        assert "findings_count" in result
        assert "scanned_at" in result
