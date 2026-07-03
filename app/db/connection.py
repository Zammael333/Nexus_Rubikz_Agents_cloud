from __future__ import annotations

import enum
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_CLOUD_SQL_AVAILABLE = False
_ASYNC_PG_AVAILABLE = False
_SQLITE_AVAILABLE = False

try:
    import asyncpg

    _ASYNC_PG_AVAILABLE = True
except ImportError:
    pass

try:
    from google.cloud.sql.connector import Connector as CloudSqlConnector

    _CLOUD_SQL_AVAILABLE = True
except ImportError:
    pass

try:
    import aiosqlite

    _SQLITE_AVAILABLE = True
except ImportError:
    pass


class DbEngine(enum.Enum):
    CLOUD_SQL = "cloud_sql"
    ASYNC_PG = "asyncpg"
    SQLITE = "sqlite"
    NONE = "none"


@dataclass
class CloudSqlConfig:
    project: str = ""
    region: str = ""
    instance: str = ""
    database: str = ""
    user: str = ""
    password: str = ""
    ip_type: str = "PUBLIC"
    driver: str = "asyncpg"
    dsn: str = field(default="")

    def __post_init__(self) -> None:
        from app.config import settings
        if not self.project:
            object.__setattr__(self, "project", settings.gcp_project_id)
        if not self.region:
            object.__setattr__(self, "region", settings.gcp_region)
        if not self.instance:
            object.__setattr__(self, "instance", os.getenv("CLOUD_SQL_INSTANCE", "nexus-db"))
        if not self.database:
            object.__setattr__(self, "database", os.getenv("CLOUD_SQL_DATABASE", "nexus"))
        if not self.user:
            object.__setattr__(self, "user", os.getenv("CLOUD_SQL_USER", ""))
        if not self.password:
            object.__setattr__(self, "password", os.getenv("CLOUD_SQL_PASSWORD", ""))
        if not self.dsn:
            object.__setattr__(self, "dsn", settings.database_url)


@dataclass
class PoolStats:
    engine: DbEngine
    open_connections: int = 0
    free_connections: int = 0
    acquired_count: int = 0
    released_count: int = 0


class AsyncDbPool:
    def __init__(
        self,
        config: CloudSqlConfig | None = None,
        min_size: int = 2,
        max_size: int = 10,
    ):
        self._config = config or CloudSqlConfig()
        self._min_size = min_size
        self._max_size = max_size
        self._engine = DbEngine.NONE
        self._pool: asyncpg.Pool | None = None
        self._sqlite_path: str = ""
        self._acquired = 0
        self._released = 0

    async def start(self) -> None:
        dsn = self._config.dsn

        if self._config.project and _CLOUD_SQL_AVAILABLE and _ASYNC_PG_AVAILABLE:
            self._engine = DbEngine.CLOUD_SQL
            self._pool = await self._create_cloud_sql_pool()
            logger.info(
                f"[DB_POOL] Cloud SQL pool started ({self._min_size}-{self._max_size})"
            )
            return

        if dsn and dsn.startswith("postgresql"):
            self._engine = DbEngine.ASYNC_PG
            self._pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=self._min_size,
                max_size=self._max_size,
            )
            logger.info(
                f"[DB_POOL] asyncpg pool started ({self._min_size}-{self._max_size})"
            )
            return

        if _SQLITE_AVAILABLE:
            self._engine = DbEngine.SQLITE
            self._sqlite_path = self._resolve_sqlite_path(dsn)
            logger.info(f"[DB_POOL] aiosqlite fallback at '{self._sqlite_path}'")
            return

        self._engine = DbEngine.NONE
        logger.warning(
            "[DB_POOL] No database backend available — running without persistence"
        )

    async def _create_cloud_sql_pool(self) -> asyncpg.Pool:
        connector = CloudSqlConnector()

        async def getconn() -> asyncpg.Connection:
            conn = await connector.connect(
                instance_connection_string=(
                    f"{self._config.project}:{self._config.region}:{self._config.instance}"
                ),
                driver=self._config.driver,
                user=self._config.user,
                password=self._config.password,
                db=self._config.database,
                ip_type=self._config.ip_type,
            )
            return conn

        pool = await asyncpg.create_pool(
            connect=getconn,
            min_size=self._min_size,
            max_size=self._max_size,
        )
        return pool

    def _resolve_sqlite_path(self, dsn: str) -> str:
        if dsn and dsn.startswith("sqlite:///"):
            return dsn[len("sqlite:///") :]
        return os.getenv("SQLITE_PATH", "nexus_vault.db")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator:
        self._acquired += 1
        conn = None
        try:
            if self._engine in (DbEngine.CLOUD_SQL, DbEngine.ASYNC_PG) and self._pool:
                async with self._pool.acquire() as conn:
                    yield conn
            elif self._engine == DbEngine.SQLITE:
                async with aiosqlite.connect(
                    self._sqlite_path, isolation_level=None
                ) as conn:
                    conn.row_factory = aiosqlite.Row
                    await conn.execute("PRAGMA journal_mode=WAL")
                    await conn.execute("PRAGMA foreign_keys=ON")
                    yield conn
            else:
                yield None
        finally:
            self._released += 1

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
        logger.info("[DB_POOL] Closed.")

    @property
    def engine(self) -> DbEngine:
        return self._engine

    @property
    def stats(self) -> PoolStats:
        if self._pool and hasattr(self._pool, "_holders"):
            open_ = len(self._pool._holders)
            free_ = sum(1 for h in self._pool._holders if not h._in_use)
        else:
            open_ = free_ = 0
        return PoolStats(
            engine=self._engine,
            open_connections=open_,
            free_connections=free_,
            acquired_count=self._acquired,
            released_count=self._released,
        )

    @property
    def is_connected(self) -> bool:
        return self._engine != DbEngine.NONE
