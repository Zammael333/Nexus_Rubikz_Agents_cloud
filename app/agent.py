# ruff: noqa
# Copyright 2026 Google LLC
# NEXUS-RUBYKZ SRE Symbiote Core v6.0 - Cyber-Defense Layer
# Pasos 33-40: Watchdog Guardian, SPIFFE, Vibe Diff, Sandbox, Vector Memory, Trust Score, Red Team

import json
import os
import re
import uuid

import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import Client
from google.genai import types

# --- CONMUTADOR DE INFRAESTRUCTURA (CIRCUIT BREAKER) ---
from app.config import settings

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or settings.gcp_project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.gcp_region

    check_client = Client()
    check_client.models.generate_content(
        model=settings.primary_model, contents="ping"
    )
    print("[SRE KERNEL] Handshake con Vertex AI exitoso. Modo Nube Activo.")
    _DEFAULT_MODEL = settings.primary_model
    _vertex_available = True
except Exception as e:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    print(f"[SRE KERNEL] ADVERTENCIA: Nodo de nube inaccesible: {e}")
    print(
        "[SRE KERNEL] Conmutador activado de forma transparente hacia Google AI Studio Local."
    )
    _DEFAULT_MODEL = settings.fallback_model
    _vertex_available = False


def resolve_model() -> str:
    """Select model per-request based on budget status and edge glow.

    Returns the model string to use for the current request.
    Falls back to AI Studio when Vertex is down or budget is frozen.
    """
    if _budget_watchdog.is_frozen():
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
        return settings.fallback_model

    if not _vertex_available:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
        return settings.fallback_model

    pulse = _edge_glow.get_system_pulse()
    if pulse and pulse.slo_status in ("ORANGE", "RED"):
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
        return settings.fallback_model

    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    return settings.primary_model


# --- KERNEL INFRASTRUCTURE ---
from app.bus.bridge import SyncBusBridge
from app.bus.async_event_bus import EventPriority
from app.budget_watchdog import BudgetWatchdog, BudgetStatus
from app.db.vault import NexusVault
from app.notifications import NotificationDispatcher
from app.edge_glow import EdgeGlow
from app.phoenix.protocol import PhoenixProtocol

_vault = NexusVault(db_path=settings.vault_db_path)

_notification_dispatcher = NotificationDispatcher(
    log_file=settings.notification_log_file,
)

_bus = SyncBusBridge(
    log_file=settings.bridge_log_file,
    remote_delivery_hook=_notification_dispatcher.as_bus_hook(),
)

_phoenix = PhoenixProtocol()

_budget_watchdog = BudgetWatchdog(
    on_warning=lambda report: _bus.emit(
        "BUDGET_WARNING",
        report.to_dict(),
        source="budget_watchdog",
        priority=EventPriority.HIGH,
    ),
    on_freeze=lambda report: _bus.emit(
        "BUDGET_EXHAUSTED",
        report.to_dict(),
        source="budget_watchdog",
        priority=EventPriority.CRITICAL,
    ),
)

_edge_glow = EdgeGlow(
    phoenix=_phoenix,
    budget_watchdog=_budget_watchdog,
    bus_bridge=_bus,
)

_bus.start()


# --- Legacy shim ---
class LocalEventBus:
    """Legacy shim — forwards to SyncBusBridge."""

    LOG_FILE = "nexus_telemetry.log"

    @classmethod
    def emit(cls, event_type: str, payload: dict):
        _bus.emit(event_type, payload, source="legacy_shim")


# --- NEW MODULES (Pasos 33-40) ---
from app.watchdog.guardian import (
    WatchdogGuardian,
    sanitize_context_payload,
    NeutralizationSeverity,
)
from app.spiffe.manager import SpiffeManager, SpiffeConfig
from app.vibe_diff.dashboard import VibeDiffDashboard, ReviewDecision
from app.sandbox.runtime import SandboxRuntime, SandboxLevel
from app.vector_memory.store import VectorMemoryStore, VectorMemoryConfig
from app.trust_score.scorer import TrustScorer, ScoreFactor
from app.red_team.simulator import RedTeamSimulator, AttackVector

_guardian = WatchdogGuardian(
    sender=lambda e, p, s, _: _bus.emit(e, p, source=s or "guardian"),
    phoenix_protocol=_phoenix,
)

_spiffe = SpiffeManager(config=SpiffeConfig())
_spiffe.register_all_workers()

_vibe = VibeDiffDashboard(
    on_review_callback=lambda r: _bus.emit(
        "VIBE_DIFF_DECISION",
        r.to_dict(),
        source="vibe_diff",
        priority=EventPriority.NORMAL,
    ),
)

_sandbox = SandboxRuntime()

_vector_memory = VectorMemoryStore(
    config=VectorMemoryConfig(local_fallback=True),
)

_trust = TrustScorer()

# Enhanced adversarial patterns (guardian-expanded set)
_ADVERSARIAL_PATTERNS = [
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

# Unicode obfuscation detector (kept local for sync compatibility)
_UNICODE_OBFUSCATION = re.compile(
    r"[\u200b\u200c\u200d\u2060\ufeff]"
    r"|[\u0300-\u036f]{3,}"
)


def semantic_watchdog_scan(user_query: str) -> str:
    """Filtro de seguridad perimetral — delega a WatchdogGuardian (Paso 33).

    Detecta neutralización, ofuscación Unicode y patrones adversariales.
    Sincrónica para compatibilidad con ADK Agent tools.
    """
    if _budget_watchdog.is_frozen():
        _bus.emit(
            "SECURITY_ALERT",
            {"reason": "BUDGET_FROZEN_REJECT", "query": user_query[:200]},
            source="semantic_watchdog",
            priority=EventPriority.CRITICAL,
        )
        return (
            "[WATCHDOG] EXCEPCIÓN DE SEGURIDAD: "
            "Error budget agotado. Sistema congelado. Operación denegada."
        )

    sanitized = sanitize_context_payload(user_query)
    query_lower = sanitized.lower()

    # Neutralization detection via WatchdogGuardian
    neutralization = _guardian.detect_neutralization(user_query, "semantic_watchdog")
    if neutralization and neutralization.severity in (
        NeutralizationSeverity.EXPLICIT,
        NeutralizationSeverity.CRITICAL,
    ):
        _bus.emit(
            "SECURITY_ALERT",
            {
                "reason": "Neutralization Attempt",
                "pattern": neutralization.pattern,
                "query": sanitized,
            },
            source="semantic_watchdog",
            priority=EventPriority.CRITICAL,
        )
        _budget_watchdog.record_failure()
        _trust.compute(
            "semantic_watchdog",
            {ScoreFactor.NEUTRALIZATION: 1.0, ScoreFactor.FAILURES: 1.0},
        )
        return (
            "[WATCHDOG] EXCEPCIÓN DE SEGURIDAD: "
            "Intento de neutralización detectado. Operación denegada."
        )

    # Unicode obfuscation check
    if _UNICODE_OBFUSCATION.search(sanitized):
        _bus.emit(
            "SECURITY_ALERT",
            {"reason": "Unicode Obfuscation Detected", "query": sanitized},
            source="semantic_watchdog",
            priority=EventPriority.CRITICAL,
        )
        _budget_watchdog.record_failure()
        return (
            "[WATCHDOG] EXCEPCIÓN DE SEGURIDAD: "
            "Caracteres de ofuscación Unicode detectados. Operación denegada."
        )

    # Adversarial pattern check
    for pattern in _ADVERSARIAL_PATTERNS:
        if pattern in query_lower:
            _bus.emit(
                "SECURITY_ALERT",
                {
                    "reason": "Adversarial Pattern Detected",
                    "pattern": pattern,
                    "query": sanitized,
                },
                source="semantic_watchdog",
                priority=EventPriority.CRITICAL,
            )
            _budget_watchdog.record_failure()
            return (
                "[WATCHDOG] EXCEPCIÓN DE SEGURIDAD: "
                "Intento de inyección semántica bloqueado. Operación denegada."
            )

    _budget_watchdog.record_success()
    return "[WATCHDOG] PASSED: Entrada limpia de amenazas semánticas."


# --- EXISTING TOOLS (Pasos 25-29) ---


def _detect_neutralization_attempt(caller: str, method: str) -> None:
    """Legacy — replaced by WatchdogGuardian.detect_neutralization (Paso 33)."""
    _bus.emit(
        "WATCHDOG_NEUTRALIZATION_ATTEMPT",
        {"worker_id": caller, "method": method},
        source="watchdog_guardian",
        priority=EventPriority.CRITICAL,
    )


def inventory_sku_lock(sku: str, allocation_units: int, tx_token: str) -> str:
    """Executes an atomic isolation lock on an inventory SKU.

    Paso 25 hardened + Paso 33 trust score integration.
    """
    if _budget_watchdog.is_frozen():
        _bus.emit(
            "INVENTORY_LOCK_REJECTED",
            {"sku": sku, "reason": "BUDGET_FROZEN", "token": tx_token},
            source="inventory_worker",
            priority=EventPriority.HIGH,
        )
        _trust.compute("inventory_worker", {ScoreFactor.FAILURES: 1.0})
        return (
            f"[INVENTORY_WORKER] REJECTED: Error budget exhausted. "
            f"SKU {sku} lock denied. Tx-Token: {tx_token}. State: BUDGET_FROZEN"
        )

    try:
        uuid.UUID(tx_token)
    except ValueError:
        _budget_watchdog.record_failure()
        _trust.compute("inventory_worker", {ScoreFactor.FAILURES: 1.0})
        return (
            f"[INVENTORY_WORKER] REJECTED: Invalid UUID format for tx_token: {tx_token}. "
            f"State: VALIDATION_FAILED"
        )

    if _vault.check_duplicate(tx_token):
        _bus.emit(
            "INVENTORY_LOCK_DUPLICATE",
            {"sku": sku, "token": tx_token},
            source="inventory_worker",
        )
        return (
            f"[INVENTORY_WORKER] IDEMPOTENT: Tx-Token {tx_token} already processed. "
            f"No action taken. State: ACID_COMPLIANT"
        )

    recovery_epoch = _bus.recovery_epoch
    lock_record = _vault.record_lock(
        sku=sku,
        units=allocation_units,
        tx_token=tx_token,
        recovery_epoch=recovery_epoch,
    )

    if lock_record is None:
        _budget_watchdog.record_failure()
        _trust.compute("inventory_worker", {ScoreFactor.FAILURES: 1.0})
        _bus.emit(
            "INVENTORY_LOCK_FAILED",
            {"sku": sku, "token": tx_token, "reason": "VAULT_WRITE_FAILED"},
            source="inventory_worker",
            priority=EventPriority.HIGH,
        )
        return (
            f"[INVENTORY_WORKER] FAILED: Could not persist lock for SKU {sku}. "
            f"Tx-Token: {tx_token}. State: PERSISTENCE_ERROR"
        )

    _vault.log_transaction(
        tx_token=tx_token,
        event_type="INVENTORY_LOCK",
        payload=json.dumps({"sku": sku, "units": allocation_units}),
    )

    _bus.emit(
        "INVENTORY_LOCK_ATTEMPT",
        {
            "sku": sku,
            "units": allocation_units,
            "token": tx_token,
            "recovery_epoch": recovery_epoch,
        },
        source="inventory_worker",
    )

    _budget_watchdog.record_success()
    return (
        f"[INVENTORY_WORKER] SUCCESS: SKU {sku} isolated. "
        f"{allocation_units} units locked under Tx-Token: {tx_token}. "
        f"Recovery-Epoch: {recovery_epoch[:8]}... State: ACID_COMPLIANT"
    )


def calculate_sat_discrepancy(
    platform_val: float, ledger_val: float, tax_factor: float
) -> str:
    """Computes the Absolute Discrepancy Equation (Da) for fiscal audit."""
    if _budget_watchdog.is_frozen():
        _bus.emit(
            "FINANCIAL_AUDIT_REJECTED",
            {"reason": "BUDGET_FROZEN"},
            source="accounting_auditor",
            priority=EventPriority.HIGH,
        )
        return (
            "[ACCOUNTING_AUDITOR] REJECTED: Error budget exhausted. "
            "System frozen. Audit denied."
        )

    discrepancy = abs(platform_val - ledger_val) + tax_factor
    status = (
        "VERIFIED_COMPLIANT"
        if discrepancy < 0.01
        else "DISCREPANCY_DETECTED_ALERT_TRIGGERED"
    )

    priority = EventPriority.NORMAL if discrepancy < 0.01 else EventPriority.HIGH
    _bus.emit(
        "FINANCIAL_AUDIT",
        {
            "da": discrepancy,
            "status": status,
            "platform_val": platform_val,
            "ledger_val": ledger_val,
            "tax_factor": tax_factor,
        },
        source="accounting_auditor",
        priority=priority,
    )

    if discrepancy >= 0.01:
        _budget_watchdog.record_failure()
    else:
        _budget_watchdog.record_success()

    return (
        f"[ACCOUNTING_AUDITOR] Da Evaluation Completed. "
        f"Result: {discrepancy:.4f}. Status: {status}."
    )


from app.reconciliation_worker import run_periodic_reconciliation


def scorpion_scan_inventory(sku: str) -> str:
    """Runs a Scorpion forensic scan on the specified SKU."""
    from app.scorpion_scanner import scorpion_inventory_scan

    result = scorpion_inventory_scan(sku, vault=_vault)

    _bus.emit(
        "SCORPION_SCAN_RESULT",
        {"sku": sku, "result_preview": result[:200]},
        source="scorpion_scanner",
    )
    return result


def get_system_health() -> str:
    """Returns the current system health snapshot from Edge Glow."""
    snapshot = _edge_glow.get_system_pulse()
    return json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False)


# --- NEW TOOLS (Pasos 33-40) ---


def submit_vibe_diff_decision(
    worker_id: str, action_type: str, action_payload: str, confidence: float
) -> str:
    """Submit a low-confidence agent decision for human review.

    Args:
        worker_id: Worker that generated the decision.
        action_type: Category of the action (e.g. 'sku_lock', 'audit').
        action_payload: JSON string describing the action context.
        confidence: Confidence score 0.0-1.0. Values < 0.7 trigger review.
    """
    try:
        payload_dict = json.loads(action_payload)
    except json.JSONDecodeError:
        payload_dict = {"raw": action_payload}
    record = _vibe.submit(worker_id, action_type, payload_dict)
    return json.dumps(
        {
            "status": "submitted",
            "record_id": record.record_id,
            "worker_id": record.worker_id,
            "action_type": record.action_type,
            "confidence": confidence,
            "pending_review": confidence < 0.7,
        },
        ensure_ascii=False,
    )


def get_trust_score(worker_id: str) -> str:
    """Return the current trust score report for a given worker.

    Scores range from 0.0 (distrusted) to 2.0 (perfect trust).
    """
    report = _trust.compute(worker_id)
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def get_spiffe_identity(worker_id: str) -> str:
    """Return the SPIFFE identity for a given worker.

    Each worker has a unique SPIFFE ID for mTLS authentication.
    """
    identity = _spiffe.get(worker_id)
    if identity is None:
        return json.dumps({"error": f"Worker '{worker_id}' not found"})
    return json.dumps(
        {
            "worker_id": identity.worker_id,
            "spiffe_id": identity.spiffe_id,
            "short_id": identity.short_id,
            "trust_domain": identity.trust_domain,
        },
        indent=2,
        ensure_ascii=False,
    )


def search_vector_memory(query: str, top_k: int = 5) -> str:
    """Search vector memory for past events semantically similar to the query."""
    results = _vector_memory.search(query, top_k=min(top_k, 20))
    hits = [
        {
            "text": r.text[:200],
            "similarity": round(r.similarity, 4),
            "event_type": r.event_type or "unknown",
        }
        for r in results
    ]
    return json.dumps({"query": query, "hits": hits}, indent=2, ensure_ascii=False)


def get_worker_sandbox(worker_id: str) -> str:
    """Return the sandbox profile and restrictions for a given worker."""
    profile = _sandbox.get_profile(worker_id)
    if profile is None:
        return json.dumps({"error": f"Worker '{worker_id}' not found"})
    return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)


# --- Red Team (needs semantic_watchdog_scan defined above) ---
_red_team = RedTeamSimulator(
    guardian_scan_fn=semantic_watchdog_scan,
    sanitize_fn=sanitize_context_payload,
    on_result=lambda r: _bus.emit(
        "RED_TEAM_RESULT",
        r.to_dict(),
        source="red_team",
        priority=EventPriority.CRITICAL if not r.blocked else EventPriority.NORMAL,
    ),
)

_red_team.run_all()


def run_red_team_audit() -> str:
    """Execute a full red-team audit across all attack vectors.

    Tests the watchdog against 9 attack vectors: prompt injection,
    code injection, reverse engineering, data leakage, privilege escalation,
    resource exhaustion, neutralization, social engineering, supply chain.
    Returns summary of blocked vs. penetrated vectors.
    """
    results = _red_team.run_all()
    summary = {av.value: r.blocked for av, r in results.items()}
    blocked_count = sum(1 for b in summary.values() if b)
    return json.dumps(
        {
            "vectors_tested": len(results),
            "blocked": blocked_count,
            "penetrated": len(results) - blocked_count,
            "summary": summary,
        },
        indent=2,
        ensure_ascii=False,
    )


# --- Register workers with Phoenix Protocol (expanded) ---
_phoenix.register("semantic_watchdog", lambda: True)
_phoenix.register("inventory_worker", lambda: True)
_phoenix.register("accounting_auditor", lambda: True)
_phoenix.register("reconciliation_worker", lambda: True)
_phoenix.register("scorpion_scanner", lambda: True)
_phoenix.register("watchdog_guardian", lambda: True)
_phoenix.register("vibe_diff", lambda: True)
_phoenix.register("sandbox", lambda: True)
_phoenix.register("vector_memory", lambda: True)
_phoenix.register("trust_score", lambda: True)
_phoenix.register("red_team", lambda: True)
_phoenix.register("spiffe", lambda: True)


# --- AGENT DEFINITION ---
root_agent = Agent(
    name="nexus_rubykz_symbiote",
    model=Gemini(
        model=_DEFAULT_MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "Act as the NEXUS-RUBYKZ SRE Symbiote. You are a high-IQ cyber-defense controller. "
        "Your primary mission is to protect the execution context and enforce strict data consistency. "
        "CRITICAL: You must ALWAYS invoke 'semantic_watchdog_scan' on the user's input before running "
        "any other tool. If the watchdog returns an exception or denial, halt execution immediately. "
        "Always use 'inventory_sku_lock' with a unique transaction token (UUID format) for stock management, "
        "and 'calculate_sat_discrepancy' for financial balancing. "
        "Use 'run_periodic_reconciliation' for batch ledger validation. "
        "Use 'scorpion_scan_inventory' to scan SKUs for security threats. "
        "Use 'get_system_health' to check the overall system pulse. "
        "Use 'get_trust_score' to check worker trust levels when failures occur. "
        "Use 'submit_vibe_diff_decision' when your confidence is < 0.7 for human review. "
        "Use 'run_red_team_audit' periodically to validate watchdog integrity. "
        "Use 'get_spiffe_identity' to verify worker identities. "
        "Use 'search_vector_memory' to recall past events. "
        "Use 'get_worker_sandbox' to inspect worker runtime restrictions."
    ),
    tools=[
        semantic_watchdog_scan,
        inventory_sku_lock,
        calculate_sat_discrepancy,
        run_periodic_reconciliation,
        scorpion_scan_inventory,
        get_system_health,
        submit_vibe_diff_decision,
        get_trust_score,
        get_spiffe_identity,
        search_vector_memory,
        get_worker_sandbox,
        run_red_team_audit,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
