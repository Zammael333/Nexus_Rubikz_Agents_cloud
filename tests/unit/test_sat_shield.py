from app.sat_shield.validator import (
    DA_THRESHOLD,
    SatShieldResult,
    calculate_da,
    verify_ledger_consistency,
)


def test_calculate_da_verified() -> None:
    result = calculate_da(platform_val=100.0, ledger_val=100.0, tax_factor=0.0)
    assert isinstance(result, SatShieldResult)
    assert result.discrepancy == 0.0
    assert result.status == "VERIFIED_COMPLIANT"
    assert result.verified is True
    assert result.platform_val == 100.0
    assert result.ledger_val == 100.0
    assert result.tax_factor == 0.0


def test_calculate_da_discrepancy() -> None:
    result = calculate_da(platform_val=100.0, ledger_val=90.0, tax_factor=0.05)
    assert result.discrepancy == 10.05
    assert result.status == "DISCREPANCY_DETECTED_ALERT_TRIGGERED"
    assert result.verified is False


def test_calculate_da_near_threshold() -> None:
    result = calculate_da(platform_val=100.0, ledger_val=99.991, tax_factor=0.0)
    assert result.discrepancy < DA_THRESHOLD
    assert result.verified is True


def test_calculate_da_at_threshold() -> None:
    result = calculate_da(platform_val=100.0, ledger_val=99.98, tax_factor=0.01)
    assert result.discrepancy == 0.03
    assert result.verified is False


def test_calculate_da_immutable() -> None:
    result = calculate_da(platform_val=200.0, ledger_val=150.0, tax_factor=0.1)
    assert result.discrepancy == 50.1
    assert result.status == "DISCREPANCY_DETECTED_ALERT_TRIGGERED"
    d = result.to_dict()
    assert d["da"] == 50.1
    assert d["verified"] is False


def test_calculate_da_negative_values() -> None:
    result = calculate_da(platform_val=-50.0, ledger_val=50.0, tax_factor=0.0)
    assert result.discrepancy == 100.0
    assert result.verified is False


def test_verify_ledger_consistency_passes() -> None:
    entries = [{"val": 10.0}, {"val": 20.0}, {"val": 30.0}]
    assert verify_ledger_consistency(entries, 60.0) is True


def test_verify_ledger_consistency_fails() -> None:
    entries = [{"val": 10.0}, {"val": 20.0}, {"val": 30.0}]
    assert verify_ledger_consistency(entries, 61.0) is False


def test_verify_ledger_consistency_empty() -> None:
    assert verify_ledger_consistency([], 0.0) is True
    assert verify_ledger_consistency([], 0.01) is False


def test_sat_shield_result_to_dict() -> None:
    result = calculate_da(100.0, 99.0, 0.0)
    d = result.to_dict()
    assert "da" in d
    assert "status" in d
    assert "verified" in d
    assert "timestamp" in d
    assert "platform_val" in d
    assert "ledger_val" in d
    assert "tax_factor" in d
