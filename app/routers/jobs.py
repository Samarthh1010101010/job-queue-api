from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.db import get_db
from app.models import JobStatus
from app.schemas import JobCreate, JobListResponse, JobResponse, JobStatusUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
    summary="Submit a new asynchronous job",
    description="Accepts a job specification, saves it to the database with `pending` status, and immediately returns a job ticket with HTTP 202.",
)
async def submit_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = await crud.create_job(db=db, job_in=job_in)
    return JobResponse.model_validate(job)


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    summary="Get job status and results",
    description="Retrieve the current status, output results, and lifecycle timestamps for a specific job ID.",
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = await crud.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' was not found.",
        )
    return JobResponse.model_validate(job)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=JobListResponse,
    summary="List all jobs",
    description="Retrieve a paginated list of jobs, optionally filtered by status (pending, in_progress, completed, failed).",
)
async def list_all_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter jobs by status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    status_val = status_filter.value if status_filter else None
    jobs, total = await crud.list_jobs(db=db, status=status_val, page=page, page_size=page_size)
    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{job_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    summary="Update job status (internal / worker endpoint)",
    description="Updates the state of a job, e.g. marking it as in_progress, completed (with result payload), or failed (with error message).",
)
async def update_job(
    job_id: str,
    status_in: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    job = await crud.update_job_status(db=db, job_id=job_id, status_in=status_in)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' was not found.",
        )
    return JobResponse.model_validate(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete or cancel a job",
    description="Removes the specified job record from the database.",
)
async def remove_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await crud.delete_job(db=db, job_id=job_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' was not found.",
        )
