# Copyright 2026 Google LLC
# NEXUS-RUBYKZ — NexusVault (Paso 25 prerequisite)
# SQLite-backed transactional persistence for inventory locks,
# transaction log, and budget metrics.  Transitional store until
# Cloud SQL migration at Step 31.

import logging
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "nexus_vault.db"


@dataclass(frozen=True)
class LockRecord:
    """Immutable snapshot of a persisted inventory lock."""

    id: int
    sku: str
    units: int
    tx_token: str
    recovery_epoch: str
    created_at: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sku": self.sku,
            "units": self.units,
            "tx_token": self.tx_token,
            "recovery_epoch": self.recovery_epoch,
            "created_at": self.created_at,
            "status": self.status,
        }


class NexusVault:
    """SQLite-backed persistence layer for NEXUS-RUBYKZ.

    Tables:
        inventory_locks — Persisted SKU locks with idempotency keys.
        tx_log — Append-only transaction audit log.
        budget_metrics — Periodic budget watchdog snapshots.

    Thread-safe: uses a dedicated lock for write serialization and
    ``check_same_thread=False`` for multi-threaded ADK usage.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self._db_path = db_path
        self._write_lock = threading.Lock()
        self._init_schema()

    # -- Schema -------------------------------------------------------------

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS inventory_locks (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku          TEXT    NOT NULL,
                    units        INTEGER NOT NULL,
                    tx_token     TEXT    NOT NULL UNIQUE,
                    recovery_epoch TEXT  NOT NULL DEFAULT '',
                    created_at   TEXT    NOT NULL,
                    status       TEXT    NOT NULL DEFAULT 'ACTIVE'
                );

                CREATE INDEX IF NOT EXISTS idx_locks_sku
                    ON inventory_locks(sku);
                CREATE INDEX IF NOT EXISTS idx_locks_tx_token
                    ON inventory_locks(tx_token);
                CREATE INDEX IF NOT EXISTS idx_locks_created_at
                    ON inventory_locks(created_at);

                CREATE TABLE IF NOT EXISTS tx_log (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    tx_token     TEXT    NOT NULL,
                    event_type   TEXT    NOT NULL,
                    payload      TEXT    NOT NULL DEFAULT '{}',
                    created_at   TEXT    NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_txlog_token
                    ON tx_log(tx_token);

                CREATE TABLE IF NOT EXISTS budget_metrics (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_requests  INTEGER NOT NULL,
                    total_failures  INTEGER NOT NULL,
                    error_rate      REAL    NOT NULL,
                    budget_consumed REAL    NOT NULL,
                    status          TEXT    NOT NULL,
                    recorded_at     TEXT    NOT NULL
                );
            """)
        logger.info(f"[VAULT] Schema initialized at '{self._db_path}'.")

    # -- Connection ---------------------------------------------------------

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -- Inventory Locks ----------------------------------------------------

    def record_lock(
        self,
        sku: str,
        units: int,
        tx_token: str,
        recovery_epoch: str = "",
    ) -> LockRecord | None:
        """Persist an inventory lock. Returns None if tx_token is duplicate."""
        now = datetime.now(UTC).isoformat()
        with self._write_lock:
            try:
                with self._connect() as conn:
                    conn.execute(
                        """INSERT INTO inventory_locks
                           (sku, units, tx_token, recovery_epoch, created_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        (sku, units, tx_token, recovery_epoch, now),
                    )
                    row = conn.execute(
                        "SELECT * FROM inventory_locks WHERE tx_token = ?",
                        (tx_token,),
                    ).fetchone()
                    if row:
                        return LockRecord(**dict(row))
            except sqlite3.IntegrityError:
                logger.warning(f"[VAULT] Duplicate tx_token rejected: {tx_token}")
                return None
        return None

    def check_duplicate(self, tx_token: str) -> bool:
        """Return True if tx_token already exists in the vault."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM inventory_locks WHERE tx_token = ?",
                (tx_token,),
            ).fetchone()
            return row is not None

    def get_locks_for_sku(self, sku: str) -> list[LockRecord]:
        """Return all locks for a given SKU."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM inventory_locks WHERE sku = ? ORDER BY created_at DESC",
                (sku,),
            ).fetchall()
            return [LockRecord(**dict(r)) for r in rows]

    def get_recent_locks(self, limit: int = 100) -> list[LockRecord]:
        """Return the N most recent locks across all SKUs."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM inventory_locks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [LockRecord(**dict(r)) for r in rows]

    def get_locks_in_window(self, sku: str, window_seconds: float) -> list[LockRecord]:
        """Return locks for a SKU created within the last N seconds."""
        cutoff = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM inventory_locks
                   WHERE sku = ? AND created_at >= datetime(?, '-' || ? || ' seconds')
                   ORDER BY created_at DESC""",
                (sku, cutoff, int(window_seconds)),
            ).fetchall()
            return [LockRecord(**dict(r)) for r in rows]

    # -- Transaction Log ----------------------------------------------------

    def log_transaction(
        self, tx_token: str, event_type: str, payload: str = "{}"
    ) -> None:
        """Append an entry to the immutable transaction log."""
        now = datetime.now(UTC).isoformat()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO tx_log (tx_token, event_type, payload, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (tx_token, event_type, payload, now),
                )

    # -- Budget Metrics -----------------------------------------------------

    def record_budget_snapshot(
        self,
        total_requests: int,
        total_failures: int,
        error_rate: float,
        budget_consumed: float,
        status: str,
    ) -> None:
        """Persist a budget watchdog snapshot for historical analysis."""
        now = datetime.now(UTC).isoformat()
        with self._write_lock:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO budget_metrics
                       (total_requests, total_failures, error_rate,
                        budget_consumed, status, recorded_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        total_requests,
                        total_failures,
                        error_rate,
                        budget_consumed,
                        status,
                        now,
                    ),
                )

    # -- Analytics ----------------------------------------------------------

    def count_locks_by_sku(self) -> dict[str, int]:
        """Return a dict of {sku: lock_count} for all SKUs."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT sku, COUNT(*) as cnt FROM inventory_locks GROUP BY sku"
            ).fetchall()
            return {r["sku"]: r["cnt"] for r in rows}

    def find_duplicate_tokens(self) -> list[str]:
        """Return tx_tokens that appear more than once in tx_log."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT tx_token FROM tx_log
                   GROUP BY tx_token HAVING COUNT(*) > 1"""
            ).fetchall()
            return [r["tx_token"] for r in rows]
