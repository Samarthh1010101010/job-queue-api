"""
CRUD helpers — raw SQL via an asyncpg connection pool.

Every function acquires a connection from the pool, executes one or two
queries, and returns plain dicts (or None / a sentinel string).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import asyncpg


# ── helpers ──────────────────────────────────────────────────────────

def _row_to_dict(record: asyncpg.Record) -> Dict[str, Any]:
    """Convert an asyncpg Record to a JSON-friendly dict."""
    d: Dict[str, Any] = dict(record)
    # UUID → str
    if isinstance(d.get("id"), UUID):
        d["id"] = str(d["id"])
    # ensure datetimes are ISO strings for Pydantic
    for key in ("created_at", "updated_at"):
        val = d.get(key)
        if isinstance(val, datetime):
            d[key] = val.isoformat()
    # asyncpg auto-decodes JSONB to Python dicts, but default to {} / None.
    if d.get("metadata") is None:
        d["metadata"] = {}
    return d


# ── CRUD ─────────────────────────────────────────────────────────────

async def create_job(
    pool: asyncpg.Pool,
    job_type: str,
    target: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """INSERT a new job in 'queued' status and return the full row."""
    query = """
        INSERT INTO jobs (job_type, target, metadata)
        VALUES ($1, $2, $3::jsonb)
        RETURNING *;
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, job_type, target, json.dumps(metadata))
    return _row_to_dict(row)  # type: ignore[arg-type]


async def get_job(
    pool: asyncpg.Pool,
    job_id: str,
) -> Optional[Dict[str, Any]]:
    """Fetch a single job by UUID. Returns None if not found."""
    query = "SELECT * FROM jobs WHERE id = $1;"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, UUID(job_id))
    if row is None:
        return None
    return _row_to_dict(row)


async def list_jobs(
    pool: asyncpg.Pool,
    status: Optional[str] = None,
    limit: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List jobs ordered by created_at DESC, with optional status filter.
    Returns (jobs, total_count).
    """
    if status:
        count_q = "SELECT count(*) FROM jobs WHERE status = $1;"
        data_q = "SELECT * FROM jobs WHERE status = $1 ORDER BY created_at DESC LIMIT $2;"
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_q, status)
            rows = await conn.fetch(data_q, status, limit)
    else:
        count_q = "SELECT count(*) FROM jobs;"
        data_q = "SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1;"
        async with pool.acquire() as conn:
            total = await conn.fetchval(count_q)
            rows = await conn.fetch(data_q, limit)

    return [_row_to_dict(r) for r in rows], total


async def cancel_job(
    pool: asyncpg.Pool,
    job_id: str,
) -> Union[Dict[str, Any], str, None]:
    """
    Cancel a job.

    Returns:
        dict  — the updated job (status='cancelled')
        None  — job not found
        str   — the current status if the job isn't in 'queued' state (→ 409)
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1;", UUID(job_id))
        if row is None:
            return None
        if row["status"] != "queued":
            return row["status"]  # caller should return 409
        updated = await conn.fetchrow(
            "UPDATE jobs SET status = 'cancelled', updated_at = now() WHERE id = $1 RETURNING *;",
            UUID(job_id),
        )
    return _row_to_dict(updated)  # type: ignore[arg-type]
