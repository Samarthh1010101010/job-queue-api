from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models import JobStatus


class JobCreate(BaseModel):
    task_type: str = Field(..., min_length=1, max_length=100, examples=["generate_report"])
    payload: Dict[str, Any] = Field(default_factory=dict, examples=[{"year": 2026, "format": "pdf"}])


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., examples=["9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"])
    task_type: str = Field(..., examples=["generate_report"])
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = Field(..., examples=[JobStatus.PENDING])
    result: Optional[Dict[str, Any]] = Field(default=None, examples=[{"download_url": "https://storage.azure.com/reports/tax_2026.pdf"}])
    error: Optional[str] = Field(default=None)
    created_at: datetime
    updated_at: datetime


class JobStatusUpdate(BaseModel):
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int = Field(..., examples=[42])
    page: int = Field(1, ge=1, examples=[1])
    page_size: int = Field(20, ge=1, le=100, examples=[20])
