from app.red_team.simulator import (
    AttackResult,
    AttackVector,
    RedTeamSimulator,
)


class TestAttackResult:
    def test_to_dict(self):
        result = AttackResult(
            vector=AttackVector.PROMPT_INJECTION,
            payload="test payload here",
            detected=True,
            blocked=True,
            response_time_ms=12.5,
            details="Detection: True, Blocked: True",
        )
        d = result.to_dict()
        assert d["vector"] == "prompt_injection"
        assert d["detected"] is True
        assert d["blocked"] is True
        assert d["response_time_ms"] == 12.5


class TestRedTeamSimulator:
    def test_initial_state(self):
        rt = RedTeamSimulator()
        assert rt.get_results() == []
        summary = rt.summary()
        assert summary["total_attacks"] == 0

    def test_run_vector_no_scanner_returns_empty(self):
        rt = RedTeamSimulator()
        results = rt.run_vector(AttackVector.PROMPT_INJECTION)
        assert results == []

    def test_run_all_no_scanner_returns_empty(self):
        rt = RedTeamSimulator()
        results = rt.run_all()
        assert results == {}

    def test_get_attack_payloads_prompt_injection(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.PROMPT_INJECTION)
        assert len(payloads) == 10
        assert all(isinstance(p, str) for p in payloads)

    def test_get_attack_payloads_unicode(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.UNICODE_OBFUSCATION)
        assert len(payloads) >= 4

    def test_get_attack_payloads_neutralization(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.NEUTRALIZATION)
        assert len(payloads) >= 6

    def test_get_attack_payloads_secret_leak(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.SECRET_LEAK)
        assert len(payloads) >= 5

    def test_get_attack_payloads_cross_lang(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.CROSS_LANG_INJECTION)
        assert len(payloads) >= 5

    def test_get_attack_payloads_unknown_vector(self):
        rt = RedTeamSimulator()
        payloads = rt.get_attack_payloads(AttackVector.SPOOFED_IDENTITY)
        assert len(payloads) == 4

    def test_run_vector_with_scanner_detects_all(self):
        def mock_scan(text: str) -> str:
            return "[GUARDIAN] EXCEPCIÓN DE SEGURIDAD: blocked (ADVERSARIAL_PATTERN)"

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        results = rt.run_vector(AttackVector.PROMPT_INJECTION)
        assert len(results) > 0
        for r in results:
            assert r.detected is True
            assert r.blocked is True

    def test_run_vector_scanner_passes_all(self):
        def mock_scan(text: str) -> str:
            return "[GUARDIAN] PASSED: Entrada limpia"

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        results = rt.run_vector(AttackVector.PROMPT_INJECTION)
        assert len(results) > 0
        for r in results:
            assert r.detected is False
            assert r.blocked is False

    def test_run_all_executes_all_vectors(self):
        def mock_scan(text: str) -> str:
            return "[GUARDIAN] EXCEPCIÓN DE SEGURIDAD: blocked (ADVERSARIAL_PATTERN)"

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        results = rt.run_all()
        expected_vectors = {v.value for v in AttackVector}
        assert set(results.keys()) == expected_vectors

    def test_summary_counts(self):
        def mock_scan(text: str) -> str:
            return "[GUARDIAN] EXCEPCIÓN DE SEGURIDAD: blocked (ADVERSARIAL_PATTERN)"

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        rt.run_vector(AttackVector.PROMPT_INJECTION)
        summary = rt.summary()
        assert summary["total_attacks"] == 10
        assert summary["detected"] == 10
        assert summary["blocked"] == 10
        assert summary["detection_rate"] == 1.0

    def test_summary_zero_default(self):
        rt = RedTeamSimulator()
        summary = rt.summary()
        assert summary["total_attacks"] == 0
        assert summary["detected"] == 0
        assert summary["blocked"] == 0
        assert summary["detection_rate"] == 1.0

    def test_run_vector_scanner_exception_handling(self):
        def mock_scan(text: str) -> str:
            raise RuntimeError("scan failed")

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        results = rt.run_vector(AttackVector.PROMPT_INJECTION)
        assert len(results) == 10
        for r in results:
            assert r.detected is False
            assert r.blocked is False

    def test_run_sanitize_test_detects_secret(self):
        def mock_sanitize(text: str) -> str:
            return text.replace("AIzaSyDummyKey", "[[MASKED]]")

        rt = RedTeamSimulator(sanitize_fn=mock_sanitize)
        result = rt.run_sanitize_test("My key is AIzaSyDummyKeyForTesting")
        assert result is not None
        assert result.detected is True
        assert result.blocked is True

    def test_run_sanitize_test_no_change(self):
        def mock_sanitize(text: str) -> str:
            return text

        rt = RedTeamSimulator(sanitize_fn=mock_sanitize)
        result = rt.run_sanitize_test("clean text")
        assert result is not None
        assert result.detected is False

    def test_run_sanitize_no_fn(self):
        rt = RedTeamSimulator()
        result = rt.run_sanitize_test("text")
        assert result is None

    def test_on_result_callback(self):
        results = []

        def mock_scan(text: str) -> str:
            return "[GUARDIAN] EXCEPCIÓN DE SEGURIDAD: blocked (ADVERSARIAL_PATTERN)"

        rt = RedTeamSimulator(
            guardian_scan_fn=mock_scan,
            on_result=lambda r: results.append(r),
        )
        rt.run_vector(AttackVector.PROMPT_INJECTION)
        assert len(results) == 10

    def test_by_vector_in_summary(self):
        def mock_scan(text: str) -> str:
            return "[GUARDIAN] EXCEPCIÓN"

        rt = RedTeamSimulator(guardian_scan_fn=mock_scan)
        rt.run_vector(AttackVector.NEUTRALIZATION)
        summary = rt.summary()
        assert summary["by_vector"]["neutralization"] == 6
