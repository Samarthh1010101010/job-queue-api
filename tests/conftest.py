import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    """
    TestClient with lifespan=True so the app's startup (connect_db + init_db)
    and shutdown (close_db) events fire.

    DATABASE_URL is picked up from the environment — in CI that points at the
    Postgres service container; locally it points at a Neon dev database (or a
    local Postgres instance) via .env.
    """
    with TestClient(app) as test_client:
        yield test_client
