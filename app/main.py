import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from app.config import settings
from app.db import check_db_health, close_db, connect_db, init_db
from app.routers.jobs import router as jobs_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: attempt DB pool creation and table initialization
    try:
        await connect_db()
        await init_db()
    except Exception as exc:
        logger.warning(f"Initial DB connection deferred: {exc}")
    yield
    # Shutdown: close pool
    await close_db()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Job submission and status-tracking service. Built in phases as a walking skeleton.",
    lifespan=lifespan,
)

# Mount Routers
app.include_router(jobs_router)


@app.get(
    "/health",
    summary="Service Health and Database Connectivity Check",
    tags=["Health"],
)
async def health(response: Response) -> dict:
    """
    Liveness and database connectivity probe.
    Returns HTTP 200 if both the API and database connection are healthy.
    """
    db_ok = await check_db_health()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "phase": settings.app_phase, "database": "disconnected"}

    return {"status": "ok", "phase": settings.app_phase, "database": "connected"}


@app.get(
    "/",
    summary="Root Service Info",
    tags=["Info"],
)
def root() -> dict:
    return {
        "service": settings.app_title,
        "version": settings.app_version,
        "phase": settings.app_phase,
        "docs_url": "/docs",
    }
