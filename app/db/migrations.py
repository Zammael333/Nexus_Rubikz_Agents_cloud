import logging

from app.db.connection import AsyncDbPool, DbEngine
from app.db.schema import PG_SCHEMA_SQL, SCHEMA_SQL

logger = logging.getLogger(__name__)

MIGRATIONS: list[tuple[str, str]] = [
    (
        "v001_initial_schema",
        "Base tables: worker_state, event_log, budget_snapshots, scorpion_findings",
    ),
]


async def ensure_schema(pool: AsyncDbPool) -> list[str]:
    applied: list[str] = []

    async with pool.acquire() as conn:
        if conn is None:
            logger.warning(
                "[MIGRATE] No database connection — skipping schema creation"
            )
            return applied

        if pool.engine == DbEngine.SQLITE:
            await conn.executescript(SCHEMA_SQL)
        else:
            await conn.execute(PG_SCHEMA_SQL)

        for name, desc in MIGRATIONS:
            already = await _migration_applied(conn, name)
            if not already:
                await _record_migration(conn, name)
                applied.append(name)
                logger.info(f"[MIGRATE] Applied: {name} — {desc}")

    if applied:
        logger.info(f"[MIGRATE] {len(applied)} new migration(s) applied")
    else:
        logger.info("[MIGRATE] Schema up-to-date")

    return applied


async def _migration_applied(conn, name: str) -> bool:
    if hasattr(conn, "execute_fetchall"):
        rows = await conn.execute_fetchall(
            "SELECT 1 FROM nexus_migrations WHERE name = $1", (name,)
        )
        return len(rows) > 0
    cursor = await conn.execute(
        "SELECT 1 FROM nexus_migrations WHERE name = ?", (name,)
    )
    row = await cursor.fetchone()
    return row is not None


async def _record_migration(conn, name: str) -> None:
    if hasattr(conn, "execute"):
        await conn.execute("INSERT INTO nexus_migrations (name) VALUES ($1)", (name,))
    else:
        await conn.execute("INSERT INTO nexus_migrations (name) VALUES (?)", (name,))
