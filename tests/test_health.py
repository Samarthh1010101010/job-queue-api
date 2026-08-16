from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_root_reports_phase():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["phase"] == 0
