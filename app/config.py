import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "development").lower()

_env_file = Path(__file__).resolve().parent.parent / f".env.{APP_ENV}"
if APP_ENV in ("production", "staging", "development"):
    _dotenv_path = _env_file
else:
    _dotenv_path = Path(__file__).resolve().parent.parent / ".env"

if _dotenv_path.is_file():
    with open(_dotenv_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _key, _val = _line.split("=", 1)
            _key = _key.strip()
            _val = _val.strip().strip("\"'")
            if _key not in os.environ:
                os.environ[_key] = _val


def _str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _int(key: str, default: int = 0) -> int:
    raw = os.environ.get(key, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _float(key: str, default: float = 0.0) -> float:
    raw = os.environ.get(key, str(default))
    try:
        return float(raw)
    except ValueError:
        return default


def _bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key, "true" if default else "false")
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _list(key: str, separator: str = ",", default: str = "") -> list[str]:
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(separator) if x.strip()]


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: APP_ENV)

    # --- GCP ---
    gcp_project_id: str = field(default_factory=lambda: _str("GCP_PROJECT_ID", ""))
    gcp_region: str = field(default_factory=lambda: _str("GCP_REGION", "us-east1"))

    # --- Agent Runtime ---
    agent_runtime_target: str = field(
        default_factory=lambda: _str("AGENT_RUNTIME_TARGET", "agent_runtime")
    )
    agent_port: int = field(default_factory=lambda: _int("AGENT_PORT", 8000))

    # --- Model Router ---
    primary_model: str = field(
        default_factory=lambda: _str("PRIMARY_MODEL", "gemini-2.0-flash-001")
    )
    fallback_model: str = field(
        default_factory=lambda: _str("FALLBACK_MODEL", "gemini-1.5-pro-002")
    )
    router_strategy: str = field(
        default_factory=lambda: _str("ROUTER_STRATEGY", "hybrid")
    )

    # --- SPIFFE ---
    spiffe_endpoint_socket: str = field(
        default_factory=lambda: _str("SPIFFE_ENDPOINT_SOCKET", "/run/spire/agent/api.sock")
    )
    spiffe_trust_domain: str = field(
        default_factory=lambda: _str("SPIFFE_TRUST_DOMAIN", "nexus-rubykz.dev")
    )

    # --- Telemetry / OTel ---
    otel_service_name: str = field(
        default_factory=lambda: _str("OTEL_SERVICE_NAME", "nexus-rubykz")
    )
    otel_exporter_otlp_endpoint: str = field(
        default_factory=lambda: _str("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    )
    otel_log_level: str = field(
        default_factory=lambda: _str("OTEL_LOG_LEVEL", "DEBUG" if APP_ENV == "development" else "WARN")
    )

    # --- Database ---
    database_url: str = field(
        default_factory=lambda: _str(
            "DATABASE_URL",
            "sqlite:///nexus_vault_dev.db" if APP_ENV == "development" else "sqlite:///nexus_vault.db",
        )
    )
    vault_db_path: str = field(default_factory=lambda: _str("VAULT_DB_PATH", "nexus_vault.db"))

    # --- Event Bus ---
    bus_flush_interval: float = field(
        default_factory=lambda: _float("BUS_FLUSH_INTERVAL", 2.0)
    )
    bus_batch_size: int = field(default_factory=lambda: _int("BUS_BATCH_SIZE", 10))
    bus_max_queue_size: int = field(
        default_factory=lambda: _int("BUS_MAX_QUEUE_SIZE", 10000)
    )
    bus_backpressure_limit: int = field(
        default_factory=lambda: _int("BUS_BACKPRESSURE_LIMIT", 10000)
    )
    bus_log_file: str = field(
        default_factory=lambda: _str("BUS_LOG_FILE", "nexus_telemetry.log")
    )

    # --- Phoenix Protocol (RTO / Health) ---
    phoenix_rto_target_seconds: float = field(
        default_factory=lambda: _float("PHOENIX_RTO_TARGET_SECONDS", 2.5)
    )
    phoenix_health_check_interval: float = field(
        default_factory=lambda: _float("PHOENIX_HEALTH_CHECK_INTERVAL", 1.0)
    )
    phoenix_max_consecutive_failures: int = field(
        default_factory=lambda: _int("PHOENIX_MAX_CONSECUTIVE_FAILURES", 2)
    )
    phoenix_quarantine_threshold: int = field(
        default_factory=lambda: _int("PHOENIX_QUARANTINE_THRESHOLD", 3)
    )
    phoenix_quarantine_window_seconds: int = field(
        default_factory=lambda: _int("PHOENIX_QUARANTINE_WINDOW_SECONDS", 30)
    )

    # --- Budget Watchdog (SLO) ---
    slo_target_percent: float = field(
        default_factory=lambda: _float("SLO_TARGET", 99.9973)
    )
    slo_window_hours: int = field(default_factory=lambda: _int("SLO_WINDOW_HOURS", 720))
    error_budget_max_percent: float = field(
        default_factory=lambda: _float("ERROR_BUDGET_MAX", 0.0027)
    )
    watchdog_alert_threshold: float = field(
        default_factory=lambda: _float("BUDGET_WATCHDOG_ALERT_THRESHOLD", 0.50)
    )
    watchdog_freeze_threshold: float = field(
        default_factory=lambda: _float("BUDGET_WATCHDOG_FREEZE_THRESHOLD", 1.00)
    )
    watchdog_sensitivity: str = field(
        default_factory=lambda: _str("WATCHDOG_SENSITIVITY", "medium")
    )

    # --- Edge Glow (SLO monitor) ---
    edge_glow_nominal_slo: float = field(
        default_factory=lambda: _float("EDGE_GLOW_NOMINAL_SLO", 0.999973)
    )
    edge_glow_nominal_error_budget: float = field(
        default_factory=lambda: _float("EDGE_GLOW_NOMINAL_ERROR_BUDGET", 0.000027)
    )

    # --- Scorpion Scanner (race / dead-stock) ---
    scorpion_race_window_seconds: float = field(
        default_factory=lambda: _float("SCORPION_RACE_WINDOW_SECONDS", 1.0)
    )
    scorpion_dead_stock_days: int = field(
        default_factory=lambda: _int("SCORPION_DEAD_STOCK_DAYS", 30)
    )

    # --- Sat Shield (DA threshold) ---
    sat_shield_da_threshold: float = field(
        default_factory=lambda: _float("SAT_SHIELD_DA_THRESHOLD", 0.01)
    )

    # --- Notifications ---
    notification_critical_tag: str = field(
        default_factory=lambda: _str("NOTIFICATION_CRITICAL_TAG", "[CRITICAL_NOTIFICATION]")
    )
    notification_log_file: str = field(
        default_factory=lambda: _str("NOTIFICATION_LOG_FILE", "nexus_critical_notifications.log")
    )

    # --- A2A Protocol ---
    a2a_ttl_seconds: float = field(
        default_factory=lambda: _float("A2A_TTL_SECONDS", 30.0)
    )
    a2a_trust_threshold: float = field(
        default_factory=lambda: _float("A2A_TRUST_THRESHOLD", 0.0)
    )

    # --- DAG Orchestrator ---
    dag_max_retries: int = field(default_factory=lambda: _int("DAG_MAX_RETRIES", 3))
    dag_global_timeout: float = field(
        default_factory=lambda: _float("DAG_GLOBAL_TIMEOUT", 300.0)
    )
    dag_retry_delays: list[float] = field(
        default_factory=lambda: _list("DAG_RETRY_DELAYS", ",", "1.0,5.0,30.0"),
    )

    # --- Bridge ---
    bridge_log_file: str = field(
        default_factory=lambda: _str("BRIDGE_LOG_FILE", "nexus_telemetry.log")
    )

    # --- SPIRE server / agent config (for spiffe/manager.py) ---
    spire_bind_address: str = field(
        default_factory=lambda: _str("SPIRE_BIND_ADDRESS", "0.0.0.0")
    )
    spire_bind_port: int = field(default_factory=lambda: _int("SPIRE_BIND_PORT", 8081))
    spire_server_port: int = field(
        default_factory=lambda: _int("SPIRE_SERVER_PORT", 8081)
    )

    # --- Twin ---
    twin_poll_interval: float = field(
        default_factory=lambda: _float("TWIN_POLL_INTERVAL", 5.0)
    )

    # --- Sentinel killswitch ---
    killswitch_flag: bool = field(default_factory=lambda: _bool("KILLSWITCH_ENABLED", True))

    def __post_init__(self) -> None:
        errors: list[str] = []
        if self.env == "production" and not self.gcp_project_id:
            errors.append("GCP_PROJECT_ID is required in production")
        if self.bus_backpressure_limit < 1:
            errors.append("BUS_BACKPRESSURE_LIMIT must be >= 1")
        if self.slo_target_percent <= 0 or self.slo_target_percent >= 100:
            errors.append("SLO_TARGET must be between 0 and 100 (exclusive)")
        if self.error_budget_max_percent <= 0:
            errors.append("ERROR_BUDGET_MAX must be > 0")
        if self.phoenix_rto_target_seconds <= 0:
            errors.append("PHOENIX_RTO_TARGET_SECONDS must be > 0")
        if errors:
            raise ValueError(
                "Settings validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )


settings = Settings()


def load_secret(secret_name: str, default: str | None = None) -> str | None:
    project_id = settings.gcp_project_id
    if not project_id:
        return default
    try:
        from google.cloud import secretmanager  # type: ignore[import-untyped]
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")
    except Exception:
        logger.warning(f"Secret {secret_name} not found in Secret Manager, using default")
        return default


__all__ = ["APP_ENV", "Settings", "load_secret", "settings"]
