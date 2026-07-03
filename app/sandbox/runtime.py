import logging
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SandboxLevel(Enum):
    NONE = "none"
    GVISOR = "gvisor"
    CONTAINER = "container"
    STRICT = "strict"


@dataclass
class AnomalyRecord:
    worker_id: str
    anomaly_type: str
    details: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "anomaly_type": self.anomaly_type,
            "details": self.details,
            "timestamp": self.timestamp,
        }


_AUTO_SANDBOX_THRESHOLD = 3  # consecutive anomalies before auto-escalation
_AUTO_SANDBOX_WINDOW = 300.0  # seconds to reset anomaly count


@dataclass
class SandboxProfile:
    worker_id: str
    level: SandboxLevel = SandboxLevel.NONE
    allowed_paths: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    allowed_network: bool = False
    memory_limit_mb: int = 256
    cpu_limit_cores: float = 1.0
    read_only_fs: bool = True
    timeout_seconds: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "level": self.level.value,
            "allowed_paths": self.allowed_paths,
            "allowed_commands": self.allowed_commands,
            "allowed_network": self.allowed_network,
            "memory_limit_mb": self.memory_limit_mb,
            "cpu_limit_cores": self.cpu_limit_cores,
            "read_only_fs": self.read_only_fs,
            "timeout_seconds": self.timeout_seconds,
        }


_DEFAULT_PROFILES: dict[str, SandboxProfile] = {
    "semantic_watchdog": SandboxProfile(
        worker_id="semantic_watchdog",
        level=SandboxLevel.NONE,
        allowed_paths=[],
        allowed_commands=[],
        allowed_network=False,
    ),
    "inventory_worker": SandboxProfile(
        worker_id="inventory_worker",
        level=SandboxLevel.GVISOR,
        allowed_paths=["/app/nexus_vault.db"],
        allowed_commands=[],
        allowed_network=False,
        read_only_fs=True,
    ),
    "accounting_auditor": SandboxProfile(
        worker_id="accounting_auditor",
        level=SandboxLevel.NONE,
        allowed_paths=[],
        allowed_commands=[],
        allowed_network=False,
    ),
    "scorpion_scanner": SandboxProfile(
        worker_id="scorpion_scanner",
        level=SandboxLevel.STRICT,
        allowed_paths=["/app/nexus_vault.db"],
        allowed_commands=[],
        allowed_network=False,
        read_only_fs=True,
    ),
    "notification_dispatcher": SandboxProfile(
        worker_id="notification_dispatcher",
        level=SandboxLevel.CONTAINER,
        allowed_paths=[],
        allowed_commands=["curl", "wget"],
        allowed_network=True,
        timeout_seconds=10.0,
    ),
    "watchdog_guardian": SandboxProfile(
        worker_id="watchdog_guardian",
        level=SandboxLevel.NONE,
        allowed_paths=[],
        allowed_commands=[],
        allowed_network=False,
    ),
}


class SandboxRuntime:
    def __init__(self, profiles: dict[str, SandboxProfile] | None = None):
        self._profiles = profiles or dict(_DEFAULT_PROFILES)
        self._gvisor_available = self._check_gvisor()
        self._anomalies: dict[str, list[AnomalyRecord]] = {}
        if not self._gvisor_available:
            logger.info(
                "[SANDBOX] gVisor (runsc) not detected. Falling back to simulation mode."
            )

    @staticmethod
    def _check_gvisor() -> bool:
        try:
            result = subprocess.run(
                ["runsc", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def get_profile(self, worker_id: str) -> SandboxProfile:
        return self._profiles.get(
            worker_id,
            SandboxProfile(worker_id=worker_id, level=SandboxLevel.NONE),
        )

    def set_profile(self, profile: SandboxProfile) -> None:
        self._profiles[profile.worker_id] = profile
        logger.info(
            f"[SANDBOX] Profile set for '{profile.worker_id}': {profile.level.value}"
        )

    def validate_operation(
        self, worker_id: str, operation_type: str, path: str = "", command: str = ""
    ) -> bool:
        profile = self.get_profile(worker_id)
        if profile.level == SandboxLevel.NONE:
            return True
        if operation_type == "file_access":
            allowed = (
                any(path.startswith(p) for p in profile.allowed_paths)
                if profile.allowed_paths
                else False
            )
            if not allowed:
                logger.warning(
                    f"[SANDBOX] Blocked file access: worker={worker_id} path={path}"
                )
                return False
        if operation_type == "command":
            base_cmd = command.split()[0] if command else ""
            if base_cmd not in profile.allowed_commands:
                logger.warning(
                    f"[SANDBOX] Blocked command: worker={worker_id} cmd={base_cmd}"
                )
                return False
        if operation_type == "network" and not profile.allowed_network:
            logger.warning(f"[SANDBOX] Blocked network access: worker={worker_id}")
            return False
        return True

    def _build_runsc_args(self, profile: SandboxProfile) -> list[str]:
        args = ["runsc"]
        if profile.read_only_fs:
            args.append("--read-only-root")
        if profile.memory_limit_mb:
            args.extend(["-m", f"{profile.memory_limit_mb}m"])
        return args

    def is_gvisor_available(self) -> bool:
        return self._gvisor_available

    @property
    def profile_count(self) -> int:
        return len(self._profiles)

    def list_profiles(self) -> dict[str, SandboxProfile]:
        return dict(self._profiles)

    # -- Self-Isolation (Paso 49) -------------------------------------------

    def record_anomaly(
        self, worker_id: str, anomaly_type: str, details: str = ""
    ) -> AnomalyRecord:
        record = AnomalyRecord(
            worker_id=worker_id,
            anomaly_type=anomaly_type,
            details=details,
        )
        self._anomalies.setdefault(worker_id, []).append(record)
        logger.warning(f"[SANDBOX] Anomaly recorded: {worker_id} type={anomaly_type}")
        return record

    def anomaly_count(
        self, worker_id: str, window: float = _AUTO_SANDBOX_WINDOW
    ) -> int:
        now = time.time()
        records = self._anomalies.get(worker_id, [])
        return sum(1 for r in records if now - r.timestamp <= window)

    def get_anomalies(self, worker_id: str) -> list[AnomalyRecord]:
        return list(self._anomalies.get(worker_id, []))

    def all_anomalies(self) -> dict[str, list[AnomalyRecord]]:
        return dict(self._anomalies)

    def auto_sandbox(
        self,
        worker_id: str,
        anomaly_type: str = "auto_detected",
        details: str = "",
        threshold: int = _AUTO_SANDBOX_THRESHOLD,
    ) -> SandboxProfile | None:
        self.record_anomaly(worker_id, anomaly_type, details)
        count = self.anomaly_count(worker_id)

        if count >= threshold:
            profile = self.get_profile(worker_id)
            current = profile.level

            if current == SandboxLevel.NONE:
                new_level = SandboxLevel.GVISOR
            elif current == SandboxLevel.GVISOR:
                new_level = SandboxLevel.CONTAINER
            elif current == SandboxLevel.CONTAINER:
                new_level = SandboxLevel.STRICT
            else:
                return None

            new_profile = SandboxProfile(
                worker_id=worker_id,
                level=new_level,
                allowed_paths=profile.allowed_paths,
                allowed_commands=profile.allowed_commands,
                allowed_network=False,
                memory_limit_mb=profile.memory_limit_mb,
                cpu_limit_cores=profile.cpu_limit_cores,
                read_only_fs=True,
                timeout_seconds=profile.timeout_seconds,
            )
            self.set_profile(new_profile)
            logger.warning(
                f"[SANDBOX] Auto-sandbox {worker_id}: {current.value} -> {new_level.value} "
                f"(anomalies={count})"
            )
            return new_profile

        return None

    def self_isolate(
        self, worker_id: str, reason: str = "manual_override"
    ) -> SandboxProfile:
        profile = self.get_profile(worker_id)
        isolated = SandboxProfile(
            worker_id=worker_id,
            level=SandboxLevel.STRICT,
            allowed_paths=[],
            allowed_commands=[],
            allowed_network=False,
            read_only_fs=True,
            timeout_seconds=profile.timeout_seconds,
        )
        self.set_profile(isolated)
        logger.warning(f"[SANDBOX] Self-isolated {worker_id}: {reason}")
        return isolated

    def reset_anomalies(self, worker_id: str) -> None:
        self._anomalies.pop(worker_id, None)
        logger.info(f"[SANDBOX] Anomalies reset for {worker_id}")
