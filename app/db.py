"""
Database connection management using a raw asyncpg connection pool.

No ORM — just a pool, raw SQL in init_db(), and a health-check query.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level pool; set during lifespan startup.
pool: Optional[asyncpg.Pool] = None

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type        TEXT        NOT NULL,
    target          TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    status          TEXT        NOT NULL DEFAULT 'queued',
    result          JSONB,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_status   ON jobs (status);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_job_type  ON jobs (job_type);",
]


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register JSON codecs so JSON and JSONB columns auto-encode/decode as Python dicts."""
    for type_name in ("json", "jsonb"):
        try:
            await conn.set_type_codec(
                type_name,
                encoder=json.dumps,
                decoder=json.loads,
                schema="pg_catalog",
            )
        except Exception:
            logger.warning(f"Could not register codec for {type_name}")


async def connect_db() -> None:
    """Create the asyncpg connection pool."""
    global pool
    dsn = settings.database_url
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
        init=_init_connection,
    )
    logger.info("Database pool created.")


async def close_db() -> None:
    """Gracefully close the connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
        logger.info("Database pool closed.")


async def init_db() -> None:
    """Create the jobs table (and indexes) if they don't already exist."""
    if pool is None:
        raise RuntimeError("Database pool is not initialized. Call connect_db() first.")
    async with pool.acquire() as conn:
        await conn.execute(_CREATE_TABLE_SQL)
        for idx_sql in _CREATE_INDEXES_SQL:
            await conn.execute(idx_sql)
    logger.info("Database tables initialized.")


async def check_db_health() -> bool:
    """Run SELECT 1 to verify the database is reachable."""
    if pool is None:
        return False
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        logger.exception("Database health check failed.")
        return False


def get_pool() -> asyncpg.Pool:
    """Return the live pool, or raise if it was never created."""
    if pool is None:
        raise RuntimeError("Database pool is not available.")
    return pool
