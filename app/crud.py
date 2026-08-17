from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, JobStatus
from app.schemas import JobCreate, JobStatusUpdate


async def create_job(db: AsyncSession, job_in: JobCreate) -> Job:
    """Create and persist a new job in PENDING state."""
    job = Job(
        task_type=job_in.task_type,
        payload=job_in.payload,
        status=JobStatus.PENDING.value,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: str) -> Optional[Job]:
    """Retrieve a single job by its UUID string."""
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_jobs(
    db: AsyncSession,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Job], int]:
    """List jobs with optional status filter and pagination."""
    query = select(Job)
    count_query = select(func.count(Job.id))

    if status:
        query = query.where(Job.status == status)
        count_query = count_query.where(Job.status == status)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated slice
    offset = (page - 1) * page_size
    query = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    jobs = list(result.scalars().all())

    return jobs, total


async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status_in: JobStatusUpdate,
) -> Optional[Job]:
    """Update job status, result payload, and/or error information."""
    job = await get_job(db, job_id)
    if not job:
        return None

    job.status = status_in.status.value if isinstance(status_in.status, JobStatus) else str(status_in.status)
    if status_in.result is not None:
        job.result = status_in.result
    if status_in.error is not None:
        job.error = status_in.error

    await db.flush()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job_id: str) -> bool:
    """Delete a job by ID."""
    job = await get_job(db, job_id)
    if not job:
        return False
    await db.delete(job)
    await db.flush()
    return True
