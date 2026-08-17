import uuid


def test_create_job_returns_202_accepted(client):
    payload = {
        "task_type": "generate_report",
        "payload": {"year": 2026, "format": "pdf"},
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["task_type"] == "generate_report"
    assert data["payload"] == {"year": 2026, "format": "pdf"}
    assert data["status"] == "pending"
    assert data["result"] is None
    assert data["error"] is None
    assert "created_at" in data
    assert "updated_at" in data


def test_get_job_by_id(client):
    # 1. Create a job
    create_resp = client.post(
        "/jobs",
        json={"task_type": "compress_video", "payload": {"resolution": "1080p"}},
    )
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    # 2. Get the job
    get_resp = client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == job_id
    assert data["task_type"] == "compress_video"
    assert data["payload"] == {"resolution": "1080p"}
    assert data["status"] == "pending"


def test_get_nonexistent_job_returns_404(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/jobs/{random_id}")
    assert response.status_code == 404
    assert f"Job with ID '{random_id}' was not found" in response.json()["detail"]


def test_list_jobs_and_pagination(client):
    # Create distinct jobs
    for i in range(3):
        client.post(
            "/jobs",
            json={"task_type": f"batch_task_{i}", "payload": {"index": i}},
        )

    response = client.get("/jobs?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert len(data["jobs"]) == 2
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_filter_jobs_by_status(client):
    # Create a job
    resp = client.post("/jobs", json={"task_type": "filter_test", "payload": {}})
    job_id = resp.json()["id"]

    # Update to in_progress
    patch_resp = client.patch(
        f"/jobs/{job_id}/status",
        json={"status": "in_progress"},
    )
    assert patch_resp.status_code == 200

    # Query status=in_progress
    list_resp = client.get("/jobs?status=in_progress")
    assert list_resp.status_code == 200
    job_ids = [j["id"] for j in list_resp.json()["jobs"]]
    assert job_id in job_ids


def test_update_job_status_and_result(client):
    # Create job
    create_resp = client.post(
        "/jobs",
        json={"task_type": "ai_inference", "payload": {"prompt": "summarize"}},
    )
    job_id = create_resp.json()["id"]

    # Complete job with result
    result_data = {"summary": "Done", "confidence": 0.98}
    patch_resp = client.patch(
        f"/jobs/{job_id}/status",
        json={"status": "completed", "result": result_data},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == "completed"
    assert updated["result"] == result_data

    # Verify through GET
    get_resp = client.get(f"/jobs/{job_id}")
    assert get_resp.json()["status"] == "completed"
    assert get_resp.json()["result"] == result_data


def test_delete_job(client):
    # Create job
    create_resp = client.post(
        "/jobs",
        json={"task_type": "temp_job", "payload": {}},
    )
    job_id = create_resp.json()["id"]

    # Delete job
    del_resp = client.delete(f"/jobs/{job_id}")
    assert del_resp.status_code == 204

    # Verify 404 on GET
    get_resp = client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_job_returns_404(client):
    random_id = str(uuid.uuid4())
    response = client.delete(f"/jobs/{random_id}")
    assert response.status_code == 404
