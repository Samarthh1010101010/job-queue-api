from app.config import settings


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_reports_database_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["phase"] == settings.app_phase


def test_root_reports_service_metadata(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["phase"] == settings.app_phase
    assert "service" in data
    assert data["docs_url"] == "/docs"
