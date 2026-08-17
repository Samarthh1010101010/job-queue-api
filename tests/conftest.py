import asyncio
import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database tables are created before running tests."""
    asyncio.run(init_db())


@pytest.fixture
def client():
    """TestClient context manager fixture ensuring lifespan events run."""
    with TestClient(app) as test_client:
        yield test_client
