"""
Tests for /jobs endpoints.

Covers: POST (create), GET by ID, GET list with filter/limit,
DELETE (cancel with 409 conflict when not queued).
"""

import uuid


# ── POST /jobs ───────────────────────────────────────────────────────

def test_create_job_returns_202(client):
    payload = {
        "job_type": "generate_report",
        "target": "Q3-2026-revenue",
        "metadata": {"format": "pdf"},
    }
    resp = client.post("/jobs", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert data["job_type"] == "generate_report"
    assert data["target"] == "Q3-2026-revenue"
    assert data["metadata"] == {"format": "pdf"}
    assert data["status"] == "queued"
    assert data["result"] is None
    assert data["error_message"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_job_with_empty_metadata(client):
    resp = client.post("/jobs", json={"job_type": "ping", "target": "server-1"})
    assert resp.status_code == 202
    assert resp.json()["metadata"] == {}


def test_create_job_missing_required_fields(client):
    resp = client.post("/jobs", json={})
    assert resp.status_code == 422

    resp2 = client.post("/jobs", json={"job_type": "test"})
    assert resp2.status_code == 422  # missing target


# ── GET /jobs/{id} ───────────────────────────────────────────────────

def test_get_job_by_id(client):
    # Create first
    create_resp = client.post("/jobs", json={
        "job_type": "resize_image",
        "target": "img-001.png",
    })
    job_id = create_resp.json()["id"]

    # Fetch
    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["job_type"] == "resize_image"
    assert data["target"] == "img-001.png"


def test_get_nonexistent_job_returns_404(client):
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/jobs/{fake_id}")
    assert resp.status_code == 404


# ── GET /jobs ────────────────────────────────────────────────────────

def test_list_jobs(client):
    # Create two jobs
    client.post("/jobs", json={"job_type": "a", "target": "t1"})
    client.post("/jobs", json={"job_type": "b", "target": "t2"})

    resp = client.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert "total" in data
    assert data["total"] >= 2


def test_list_jobs_with_status_filter(client):
    # Create a job (status=queued)
    client.post("/jobs", json={"job_type": "filter_test", "target": "x"})

    resp = client.get("/jobs?status=queued")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for job in data["jobs"]:
        assert job["status"] == "queued"


def test_list_jobs_with_limit(client):
    # Create several jobs
    for i in range(3):
        client.post("/jobs", json={"job_type": "limit_test", "target": f"t{i}"})

    resp = client.get("/jobs?limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["jobs"]) <= 2


def test_list_jobs_invalid_status_returns_422(client):
    resp = client.get("/jobs?status=bananas")
    assert resp.status_code == 422


# ── DELETE /jobs/{id} (cancel) ───────────────────────────────────────

def test_cancel_queued_job_returns_200(client):
    create_resp = client.post("/jobs", json={
        "job_type": "cancel_test",
        "target": "target-1",
    })
    job_id = create_resp.json()["id"]

    resp = client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["id"] == job_id


def test_cancel_already_cancelled_job_returns_409(client):
    # Create and cancel
    create_resp = client.post("/jobs", json={
        "job_type": "double_cancel",
        "target": "target-2",
    })
    job_id = create_resp.json()["id"]
    client.delete(f"/jobs/{job_id}")  # first cancel → 200

    # Second cancel → 409
    resp = client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 409
    assert "cancelled" in resp.json()["detail"]


def test_cancel_nonexistent_job_returns_404(client):
    fake_id = str(uuid.uuid4())
    resp = client.delete(f"/jobs/{fake_id}")
    assert resp.status_code == 404
