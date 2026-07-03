# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — Budget Watchdog Unit Tests (Paso 30)


from app.budget_watchdog import BudgetStatus, BudgetWatchdog


class TestBudgetWatchdog:
    """Tests for the Budget Watchdog (Step 23, Scorpion SC-05)."""

    def test_initial_state_healthy(self):
        bw = BudgetWatchdog()
        report = bw.check_budget()
        assert report.status == BudgetStatus.HEALTHY
        assert report.total_requests == 0
        assert report.total_failures == 0

    def test_record_success(self):
        bw = BudgetWatchdog()
        report = bw.record_success()
        assert report.total_requests == 1
        assert report.total_failures == 0
        assert report.status == BudgetStatus.HEALTHY

    def test_record_failure(self):
        bw = BudgetWatchdog()
        report = bw.record_failure()
        assert report.total_requests == 1
        assert report.total_failures == 1
        assert report.error_rate_percent == 100.0

    def test_healthy_under_budget(self):
        bw = BudgetWatchdog(error_budget_percent=10.0)  # 10% budget
        for _ in range(99):
            bw.record_success()
        report = bw.record_failure()  # 1% error rate, well under 10%
        assert report.status == BudgetStatus.HEALTHY

    def test_warning_at_50_percent(self):
        bw = BudgetWatchdog(error_budget_percent=10.0)
        # 5% error rate → 50% of 10% budget
        for _ in range(95):
            bw.record_success()
        for _ in range(5):
            report = bw.record_failure()
        assert report.status == BudgetStatus.WARNING

    def test_frozen_at_100_percent(self):
        bw = BudgetWatchdog(error_budget_percent=10.0)
        # 10% error rate → 100% of 10% budget
        for _ in range(90):
            bw.record_success()
        for _ in range(10):
            report = bw.record_failure()
        assert report.status == BudgetStatus.FROZEN

    def test_is_frozen_shortcut(self):
        bw = BudgetWatchdog(error_budget_percent=1.0)
        # 100% failures → way over budget
        bw.record_failure()
        assert bw.is_frozen() is True

    def test_reset_clears_state(self):
        bw = BudgetWatchdog(error_budget_percent=1.0)
        bw.record_failure()
        assert bw.is_frozen()
        bw.reset()
        report = bw.check_budget()
        assert report.status == BudgetStatus.HEALTHY
        assert report.total_requests == 0

    def test_warning_callback_fires(self):
        warnings = []
        bw = BudgetWatchdog(
            error_budget_percent=10.0,
            on_warning=lambda r: warnings.append(r),
        )
        for _ in range(95):
            bw.record_success()
        for _ in range(5):
            bw.record_failure()
        assert len(warnings) == 1
        assert warnings[0].status == BudgetStatus.WARNING

    def test_freeze_callback_fires(self):
        freezes = []
        bw = BudgetWatchdog(
            error_budget_percent=10.0,
            on_freeze=lambda r: freezes.append(r),
        )
        for _ in range(90):
            bw.record_success()
        for _ in range(10):
            bw.record_failure()
        assert len(freezes) == 1
        assert freezes[0].status == BudgetStatus.FROZEN

    def test_budget_report_to_dict(self):
        bw = BudgetWatchdog()
        bw.record_success()
        report = bw.check_budget()
        d = report.to_dict()
        assert "total_requests" in d
        assert "status" in d
        assert d["status"] == "healthy"

    def test_allowed_failures_remaining(self):
        bw = BudgetWatchdog(error_budget_percent=10.0)
        for _ in range(100):
            bw.record_success()
        report = bw.check_budget()
        # 10% of 100 = 10 failures allowed, 0 used
        assert report.allowed_failures_remaining == 10
