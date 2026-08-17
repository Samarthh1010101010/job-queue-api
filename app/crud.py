"""
CRUD helpers — raw SQL via an asyncpg connection pool.

Every function acquires a connection from the pool, executes queries,
and returns plain dicts (or None / a sentinel string).
"""

from __future__ import annotations

import json
from datetime import datetime
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
    # ensure datetimes are preserved
    for key in ("created_at", "updated_at"):
        val = d.get(key)
        if isinstance(val, datetime):
            d[key] = val
    # JSONB fields: decode from string if raw JSON string returned
    for key in ("metadata", "result"):
        val = d.get(key)
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except Exception:
                pass
        elif val is None and key == "metadata":
            d[key] = {}
    return d


# ── CRUD ─────────────────────────────────────────────────────────────

async def create_job(
    pool: asyncpg.Pool,
    job_type: str,
    target: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """INSERT a new job in 'queued' status and return the full row."""
    query = """
        INSERT INTO jobs (job_type, target, metadata)
        VALUES ($1, $2, $3)
        RETURNING *;
    """
    meta = metadata if metadata is not None else {}
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, job_type, target, meta)
    return _row_to_dict(row)  # type: ignore[arg-type]


async def get_job(
    pool: asyncpg.Pool,
    job_id: str,
) -> Optional[Dict[str, Any]]:
    """Fetch a single job by UUID. Returns None if not found or invalid UUID."""
    try:
        parsed_uuid = UUID(job_id)
    except (ValueError, TypeError):
        return None
    query = "SELECT * FROM jobs WHERE id = $1;"
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, parsed_uuid)
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
        None  — job not found (or invalid UUID)
        str   — the current status if the job isn't in 'queued' state (→ 409)
    """
    try:
        parsed_uuid = UUID(job_id)
    except (ValueError, TypeError):
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1;", parsed_uuid)
        if row is None:
            return None
        if row["status"] != "queued":
            return row["status"]  # caller should return 409
        updated = await conn.fetchrow(
            "UPDATE jobs SET status = 'cancelled', updated_at = now() WHERE id = $1 RETURNING *;",
            parsed_uuid,
        )
    return _row_to_dict(updated)  # type: ignore[arg-type]
