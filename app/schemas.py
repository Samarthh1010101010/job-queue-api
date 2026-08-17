from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models import JobStatus


# ── Request schemas ──────────────────────────────────────────────────

class JobCreate(BaseModel):
    job_type: str = Field(
        ..., min_length=1, max_length=100,
        examples=["generate_report"],
    )
    target: str = Field(
        ..., min_length=1, max_length=255,
        examples=["Q3-2026-revenue"],
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"format": "pdf", "fiscal_year": 2026}],
    )


# ── Response schemas ─────────────────────────────────────────────────

class JobResponse(BaseModel):
    id: str = Field(..., examples=["9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"])
    job_type: str = Field(..., examples=["generate_report"])
    target: str = Field(..., examples=["Q3-2026-revenue"])
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = Field(..., examples=[JobStatus.QUEUED])
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int = Field(..., examples=[42])
