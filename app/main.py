import sys
import os

site_packages = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".python_packages", "lib", "site-packages")
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.insert(0, site_packages)

from fastapi import FastAPI

app = FastAPI(
    title="Job Queue & Status API",
    version="0.1.0",
    description="Asynchronous job-processing service. Built in phases.",
)


@app.get("/health")
def health() -> dict:
    """
    Liveness check.

    Phase 0 intentionally has no dependencies (no DB, no queue). The goal
    right now is to prove the deploy pipeline works end to end — GitHub
    Actions building and shipping this exact endpoint to Azure App Service —
    before any business logic is layered on top. Once Postgres is added in
    Phase 1, this will report DB connectivity too.
    """
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {"service": "job-queue-api", "phase": 0}
