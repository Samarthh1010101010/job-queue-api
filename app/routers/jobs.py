from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import crud
from app.db import get_pool
from app.models import JobStatus
from app.schemas import JobCreate, JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
    summary="Submit a new asynchronous job",
    description=(
        "Accepts a job specification, saves it to the database with "
        "`queued` status, and immediately returns a job ticket with HTTP 202."
    ),
)
async def submit_job(job_in: JobCreate) -> JobResponse:
    pool = get_pool()
    row = await crud.create_job(
        pool,
        job_type=job_in.job_type,
        target=job_in.target,
        metadata=job_in.metadata,
    )
    return JobResponse(**row)


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    summary="Get job status and results",
    description="Retrieve the current status and details for a specific job ID.",
)
async def get_job_status(job_id: str) -> JobResponse:
    pool = get_pool()
    row = await crud.get_job(pool, job_id=job_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' was not found.",
        )
    return JobResponse(**row)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=JobListResponse,
    summary="List all jobs",
    description="Retrieve a list of jobs, optionally filtered by status.",
)
async def list_all_jobs(
    status_filter: Optional[JobStatus] = Query(
        None, alias="status", description="Filter jobs by status"
    ),
    limit: int = Query(20, ge=1, le=100, description="Max number of jobs to return"),
) -> JobListResponse:
    pool = get_pool()
    status_val = status_filter.value if status_filter else None
    jobs, total = await crud.list_jobs(pool, status=status_val, limit=limit)
    return JobListResponse(
        jobs=[JobResponse(**j) for j in jobs],
        total=total,
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobResponse,
    summary="Cancel a queued job",
    description=(
        "Sets a job's status to 'cancelled'. Only works for jobs that are "
        "still in 'queued' status; returns 409 Conflict otherwise."
    ),
)
async def cancel_job(job_id: str) -> JobResponse:
    pool = get_pool()
    result = await crud.cancel_job(pool, job_id=job_id)

    # Not found
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' was not found.",
        )

    # Already processing/completed/failed/cancelled → 409
    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Job can only be cancelled when in 'queued' status. "
                f"Current status: '{result}'."
            ),
        )

    # Success — return the now-cancelled job
    return JobResponse(**result)
