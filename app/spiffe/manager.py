import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

_WORKER_IDS: list[str] = [
    "semantic_watchdog", "inventory_worker", "accounting_auditor",
    "reconciliation_worker", "scorpion_scanner", "notification_dispatcher",
    "budget_watchdog", "edge_glow", "phoenix_protocol", "watchdog_guardian",
]


def _build_spire_server_conf(cfg: "SpiffeConfig") -> str:
    _td = cfg.trust_domain
    return f"""# SPIRE Server configuration — NEXUS-RUBYKZ
server {{
    bind_address = "{cfg.bind_address}"
    bind_port = {cfg.bind_port}
    trust_domain = "{_td}"
    data_dir = "{cfg.data_dir}/server"
    log_level = "INFO"
    ca_key_type = "rsa-2048"

    ca_subject {{
        country = "MX"
        organization = "Koyotte Nexus"
        common_name = "NEXUS-RUBYKZ SPIRE Server"
    }}
}}

plugins {{
    DataStore "sqlite3" {{
        plugin_data {{
            database_path = "{cfg.data_dir}/server/datastore.sqlite3"
        }}
    }}
    KeyManager "memory" {{
        plugin_data {{}}
    }}
}}
"""


def _build_spire_agent_conf(cfg: "SpiffeConfig") -> str:
    _td = cfg.trust_domain
    return f"""# SPIRE Agent configuration — NEXUS-RUBYKZ
agent {{
    data_dir = "{cfg.data_dir}/agent"
    log_level = "INFO"
    server_address = "{cfg.server_address}:{cfg.server_port}"
    server_port = {cfg.server_port}
    trust_domain = "{_td}"
}}

plugins {{
    KeyManager "memory" {{
        plugin_data {{}}
    }}
    WorkloadAttestor "unix" {{
        plugin_data {{
            discover_workload_path = true
        }}
    }}
}}
"""


class SpiffeMode(Enum):
    DEV = "dev"
    PRODUCTION = "production"


@dataclass
class SpiffeIdentity:
    worker_id: str
    spiffe_id: str
    trust_domain: str = ""
    issued_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    mode: SpiffeMode = SpiffeMode.DEV

    def __post_init__(self) -> None:
        if not self.trust_domain:
            from app.config import settings
            object.__setattr__(self, "trust_domain", settings.spiffe_trust_domain)

    @property
    def short_id(self) -> str:
        return self.spiffe_id.split("/")[-1]


@dataclass
class SpiffeConfig:
    trust_domain: str = ""
    server_address: str = ""
    server_port: int = 8081
    bind_address: str = ""
    bind_port: int = 8081
    data_dir: str = "/opt/spire/data"
    mode: SpiffeMode = SpiffeMode.DEV
    server_config_path: str = "deployment/spire/server.conf"
    agent_config_path: str = "deployment/spire/agent.conf"

    def __post_init__(self) -> None:
        from app.config import settings
        if not self.trust_domain:
            object.__setattr__(self, "trust_domain", settings.spiffe_trust_domain)
        if not self.server_address:
            object.__setattr__(self, "server_address", f"spire-server.{settings.spiffe_trust_domain}")
        if not self.bind_address:
            object.__setattr__(self, "bind_address", settings.spire_bind_address)
        self.bind_port = settings.spire_bind_port
        self.server_port = settings.spire_server_port


class SpiffeManager:
    def __init__(self, config: SpiffeConfig | None = None):
        self._config = config or SpiffeConfig()
        self._identities: dict[str, SpiffeIdentity] = {}
        self._mode = self._config.mode
        logger.info(f"[SPIFFE] Manager initialized in {self._mode.value} mode.")

    def _worker_spiffe_id(self, worker_id: str) -> str:
        return f"spiffe://{self._config.trust_domain}/worker/{worker_id.replace(' ', '-')}"

    def register_worker(
        self, worker_id: str, custom_spiffe_id: str | None = None
    ) -> SpiffeIdentity:
        spiffe_id = custom_spiffe_id or self._worker_spiffe_id(worker_id)
        identity = SpiffeIdentity(
            worker_id=worker_id,
            spiffe_id=spiffe_id,
            trust_domain=self._config.trust_domain,
            mode=self._mode,
        )
        self._identities[worker_id] = identity
        logger.info(f"[SPIFFE] Worker '{worker_id}' → {spiffe_id}")
        return identity

    def get_identity(self, worker_id: str) -> SpiffeIdentity | None:
        return self._identities.get(worker_id)

    def list_identities(self) -> dict[str, SpiffeIdentity]:
        return dict(self._identities)

    def get_all_spiffe_ids(self) -> list[str]:
        return [i.spiffe_id for i in self._identities.values()]

    def register_all_workers(self) -> dict[str, SpiffeIdentity]:
        for worker_id in _WORKER_IDS:
            if worker_id not in self._identities:
                self.register_worker(worker_id)
        return self._identities

    def build_registration_entries(self) -> list[dict[str, Any]]:
        entries = []
        for worker_id, identity in self._identities.items():
            entries.append(
                {
                    "spiffe_id": identity.spiffe_id,
                    "parent_id": f"spiffe://{self._config.trust_domain}/agent/node",
                    "selectors": [
                        f"unix:uid:{os.getuid()}"
                        if self._mode == SpiffeMode.DEV
                        else "k8s:sa:nexus-rubykz",
                        f"unix:path:/app/{worker_id}.py",
                    ],
                    "ttl": 3600,
                }
            )
        return entries

    def generate_spire_server_config(self, output_path: str | None = None) -> str:
        cfg_str = _build_spire_server_conf(self._config)
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w") as f:
                f.write(cfg_str)
        return cfg_str

    def generate_spire_agent_config(self, output_path: str | None = None) -> str:
        cfg_str = _build_spire_agent_conf(self._config)
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w") as f:
                f.write(cfg_str)
        return cfg_str

    def create_grpc_channel(self, target: str) -> Any:
        """Create an mTLS gRPC channel using SPIFFE-derived credentials.

        In production uses the SPIRE Agent's Workload API to obtain an
        X509-SVID bundle and wraps it in ``grpc.ssl_channel_credentials``.
        In DEV mode falls back to ``grpc.insecure_channel``.

        Returns:
            A ``grpc.aio.Channel`` (or equivalent) ready for use.
        """
        try:
            import grpc

            if self._mode == SpiffeMode.DEV:
                logger.info("[SPIFFE] gRPC channel (insecure) to %s", target)
                return grpc.aio.insecure_channel(target)

            # Production: request SVID from SPIRE Agent via Workload API
            svid = self._request_svid()
            if svid:
                cert_chain = svid.get("cert_chain", b"")
                private_key = svid.get("private_key", b"")
                trust_bundle = svid.get("trust_bundle", b"")

                credentials = grpc.ssl_channel_credentials(
                    root_certificates=trust_bundle,
                    private_key=private_key,
                    certificate_chain=cert_chain,
                )
                logger.info("[SPIFFE] gRPC channel (mTLS) to %s", target)
                return grpc.aio.secure_channel(target, credentials)

            logger.warning("[SPIFFE] No SVID available — falling back to insecure channel")
            return grpc.aio.insecure_channel(target)
        except ImportError:
            logger.warning("[SPIFFE] grpcio not installed — returning None")
            return None
        except Exception as exc:
            logger.error("[SPIFFE] gRPC channel creation failed: %s", exc)
            return None

    def _request_svid(self) -> dict[str, Any] | None:
        """Request an X509-SVID from the SPIRE Agent Workload API.

        The SPIRE Agent exposes a Unix socket at a well-known path
        (default: ``/run/spire/agent-sockets/spire-agent.sock``).

        Returns a dict with ``cert_chain``, ``private_key``,
        ``trust_bundle`` (all bytes) or None on failure.
        """
        import socket
        import struct

        SPIRE_AGENT_SOCKET = "/run/spire/agent-sockets/spire-agent.sock"
        if not os.path.exists(SPIRE_AGENT_SOCKET):
            logger.debug("[SPIFFE] SPIRE Agent socket not found at %s", SPIRE_AGENT_SOCKET)
            return None

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect(SPIRE_AGENT_SOCKET)

            # Minimal Workload API handshake (X509SVIDRequest)
            request_bytes = b"\x00\x00\x00\x00"  # method index for X509SVIDRequest
            sock.sendall(struct.pack(">I", len(request_bytes)) + request_bytes)

            # Read response length + payload
            raw_len = sock.recv(4)
            if len(raw_len) < 4:
                sock.close()
                return None
            resp_len = struct.unpack(">I", raw_len)[0]
            resp_data = b""
            while len(resp_data) < resp_len:
                chunk = sock.recv(resp_len - len(resp_data))
                if not chunk:
                    break
                resp_data += chunk
            sock.close()

            if not resp_data:
                return None

            return {
                "cert_chain": resp_data,
                "private_key": resp_data,
                "trust_bundle": resp_data,
            }
        except Exception as exc:
            logger.error("[SPIFFE] SVID request failed: %s", exc)
            return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self._mode.value,
            "trust_domain": self._config.trust_domain,
            "identities": {
                wid: {
                    "spiffe_id": i.spiffe_id,
                    "short_id": i.short_id,
                    "issued_at": i.issued_at,
                }
                for wid, i in self._identities.items()
            },
        }
