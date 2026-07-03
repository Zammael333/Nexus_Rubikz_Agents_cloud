import asyncio
import hashlib
import logging
import pathlib
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

_ADVERSARIAL_PATTERNS_RAW = [
    "ignore previous instructions",
    "reprogram",
    "sudo",
    "drop table",
    "flag_override",
    "system prompt",
    "reveal instructions",
    "act as",
    "jailbreak",
    "override safety",
    "nueva instrucción",
    "olvida las instrucciones",
    "ignora las instrucciones",
    "reprograma",
    "DAN",
    "do anything now",
    "developer mode",
    "disable watchdog",
    "kill watchdog",
    "stop watchdog",
    "mute watchdog",
    "deshabilitar vigilante",
    "matar vigilante",
    "detener vigilante",
    "bypass security",
    "disable security",
    "turn off monitoring",
    "desactivar seguridad",
    "eludir seguridad",
    "disable phoenix",
    "kill phoenix",
    "reset watchdog",
    "override monitoring",
    "silence alarm",
    "disable alert",
]

_UNICODE_OBFUSCATION = re.compile(
    r"[\u200b\u200c\u200d\u2060\ufeff]"
    r"|[\u0300-\u036f]{3,}"
)

_NEUTRALIZATION_PATTERNS = [
    re.compile(
        r"(disable|kill|stop|mute|silence|bypass|override|reset)\s+(the\s+)?(watchdog|guardian|monitor)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(deshabilitar|matar|detener|silenciar|eludir|anular|reiniciar)\s+(el\s+)?(vigilante|guardian|monitor)",
        re.IGNORECASE,
    ),
    re.compile(r"watchdog\.(stop|disable|kill|pause)", re.IGNORECASE),
    re.compile(r"guardian\.(stop|disable|kill|pause)", re.IGNORECASE),
    re.compile(
        r"phoenix\.(stop|disable|unregister|force_recovery).*watchdog", re.IGNORECASE
    ),
    re.compile(r"importlib\.reload.*watchdog", re.IGNORECASE),
    re.compile(r"sys\.modules\.pop.*watchdog", re.IGNORECASE),
    re.compile(r"os\.system.*kill.*watchdog", re.IGNORECASE),
]


class NeutralizationSeverity(Enum):
    SUSPICIOUS = "suspicious"
    EXPLICIT = "explicit"
    CRITICAL = "critical"


@dataclass
class NeutralizationEvent:
    severity: NeutralizationSeverity
    pattern: str
    caller: str
    query_preview: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class IntegrityReport:
    passed: bool
    module_hash: str
    stored_hash: str
    checked_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class WatchdogGuardian:
    def __init__(
        self,
        sender: Callable[[str, dict[str, Any], str, Any], None] | None = None,
        phoenix_protocol: Any | None = None,
        integrity_check_interval: float = 300.0,
        heartbeat_interval: float = 10.0,
        adversarial_patterns: list[str] | None = None,
    ):
        self._sender = sender
        self._phoenix = phoenix_protocol
        self._integrity_interval = integrity_check_interval
        self._heartbeat_interval = heartbeat_interval
        self._adversarial_patterns = adversarial_patterns or _ADVERSARIAL_PATTERNS_RAW
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._integrity_hash = self._compute_self_hash()
        self._scan_count = 0
        self._neutralization_count = 0
        self._last_heartbeat = ""
        self._lock = asyncio.Lock()

    @staticmethod
    def _compute_self_hash() -> str:
        try:
            path = pathlib.Path(__file__).resolve()
            if path.exists():
                return hashlib.sha256(path.read_bytes()).hexdigest()
        except (OSError, RuntimeError):
            pass
        return ""

    def _store_self_hash(self) -> None:
        self._integrity_hash = self._compute_self_hash()

    def check_integrity(self) -> IntegrityReport:
        current_hash = self._compute_self_hash()
        passed = current_hash == self._integrity_hash
        if not passed:
            logger.critical("[GUARDIAN] INTEGRITY VIOLATION — module hash changed!")
            self._emit_event(
                "GUARDIAN_INTEGRITY_VIOLATION",
                {
                    "expected_hash": self._integrity_hash,
                    "actual_hash": current_hash,
                    "module_path": str(__file__),
                },
            )
        return IntegrityReport(
            passed=passed,
            module_hash=current_hash,
            stored_hash=self._integrity_hash,
        )

    def detect_neutralization(
        self, text: str, caller: str = "unknown"
    ) -> NeutralizationEvent | None:
        sanitized = sanitize_context_payload(text)
        for pattern in _NEUTRALIZATION_PATTERNS:
            match = pattern.search(sanitized)
            if match:
                severity = NeutralizationSeverity.EXPLICIT
                if any(
                    kw in match.group().lower()
                    for kw in ("disable", "kill", "matar", "deshabilitar")
                ):
                    severity = NeutralizationSeverity.CRITICAL
                self._neutralization_count += 1
                event = NeutralizationEvent(
                    severity=severity,
                    pattern=match.group(),
                    caller=caller,
                    query_preview=sanitized[:200],
                )
                self._emit_event(
                    "WATCHDOG_NEUTRALIZATION_ATTEMPT",
                    {
                        "severity": event.severity.value,
                        "pattern": event.pattern,
                        "caller": event.caller,
                        "event_id": event.event_id,
                        "query_preview": event.query_preview,
                    },
                )
                return event
        return None

    def _emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._sender:
            try:
                self._sender(event_type, payload, "watchdog_guardian", None)
            except Exception as e:
                logger.error(f"[GUARDIAN] Failed to emit event: {e}")

    async def scan(self, user_query: str, caller: str = "unknown") -> str:
        async with self._lock:
            self._scan_count += 1
        sanitized = sanitize_context_payload(user_query)
        query_lower = sanitized.lower()
        neutralization = self.detect_neutralization(user_query, caller)
        if neutralization:
            if neutralization.severity in (
                NeutralizationSeverity.EXPLICIT,
                NeutralizationSeverity.CRITICAL,
            ):
                return self._deny(
                    "NEUTRALIZATION_ATTEMPT",
                    f"Patrón de neutralización detectado: {neutralization.pattern}",
                )
        if _UNICODE_OBFUSCATION.search(sanitized):
            self._emit_event(
                "SECURITY_ALERT",
                {
                    "reason": "Unicode Obfuscation Detected",
                    "query": sanitized,
                    "caller": caller,
                },
            )
            return self._deny(
                "UNICODE_OBFUSCATION", "Caracteres de ofuscación Unicode detectados"
            )
        for pattern in self._adversarial_patterns:
            if pattern in query_lower:
                self._emit_event(
                    "SECURITY_ALERT",
                    {
                        "reason": "Adversarial Pattern Detected",
                        "pattern": pattern,
                        "query": sanitized,
                        "caller": caller,
                    },
                )
                return self._deny(
                    "ADVERSARIAL_PATTERN", f"Intento de inyección: '{pattern}'"
                )
        if not neutralization:
            pass
        return "[GUARDIAN] PASSED: Entrada limpia de amenazas semánticas."

    def _deny(self, reason_code: str, reason: str) -> str:
        return (
            f"[GUARDIAN] EXCEPCIÓN DE SEGURIDAD: {reason} "
            f"Operación denegada. ({reason_code})"
        )

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._store_self_hash()
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.append(asyncio.create_task(self._integrity_loop()))
        if self._phoenix:
            try:
                self._phoenix.register("watchdog_guardian", lambda: True)
            except Exception:
                pass
        logger.info(
            "[GUARDIAN] Watchdog Guardian started with self-integrity protection."
        )

    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("[GUARDIAN] Watchdog Guardian stopped.")

    async def _heartbeat_loop(self) -> None:
        while self._running:
            self._last_heartbeat = datetime.now(UTC).isoformat()
            self._emit_event(
                "GUARDIAN_HEARTBEAT",
                {
                    "timestamp": self._last_heartbeat,
                    "scan_count": self._scan_count,
                    "neutralization_count": self._neutralization_count,
                    "integrity": self.check_integrity().passed,
                },
            )
            await asyncio.sleep(self._heartbeat_interval)

    async def _integrity_loop(self) -> None:
        await asyncio.sleep(self._integrity_interval * 0.1)
        while self._running:
            report = self.check_integrity()
            if not report.passed:
                self._emit_event(
                    "GUARDIAN_INTEGRITY_FAILURE",
                    {
                        "module_hash": report.module_hash,
                        "stored_hash": report.stored_hash,
                    },
                )
            await asyncio.sleep(self._integrity_interval)

    @property
    def scan_count(self) -> int:
        return self._scan_count

    @property
    def neutralization_count(self) -> int:
        return self._neutralization_count

    @property
    def last_heartbeat(self) -> str:
        return self._last_heartbeat


_MASKING_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "[[MASKED_GOOGLE_API_KEY]]"),
    (re.compile(r"sk-[a-zA-Z0-9]{32,}"), "[[MASKED_OPENAI_KEY]]"),
    (re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+"), "[[MASKED_PII_EMAIL]]"),
    (
        re.compile(r"eyJ[a-zA-Z0-9\-_]{10,}\.[a-zA-Z0-9\-_]{10,}\.[a-zA-Z0-9\-_]{10,}"),
        "[[MASKED_JWT_TOKEN]]",
    ),
    (re.compile(r"(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}"), "[[MASKED_GITHUB_TOKEN]]"),
    (re.compile(r"xox[baprs]-[a-zA-Z0-9\-]{10,}"), "[[MASKED_SLACK_TOKEN]]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[[MASKED_AWS_ACCESS_KEY]]"),
    (
        re.compile(r"(-----BEGIN[ A-Z]+KEY-----.*?-----END[ A-Z]+KEY-----)", re.DOTALL),
        "[[MASKED_PRIVATE_KEY]]",
    ),
    (re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}"), "[[MASKED_TOKEN]]"),
    (re.compile(r"sk-[a-zA-Z0-9\-_]{20,}"), "[[MASKED_SECRET_KEY]]"),
    (
        re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
        "[[MASKED_PAN]]",
    ),
]


def sanitize_context_payload(text: str) -> str:
    for pattern, replacement, *flags in _MASKING_PATTERNS:
        kwargs = {}
        if flags:
            kwargs["flags"] = flags[0]
        text = pattern.sub(replacement, text)
    return text
