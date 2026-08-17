# Job Queue & Status API

An asynchronous job-processing service. Built as a walking skeleton: each
phase adds exactly one new integration point and is deployed and verified
before the next one starts, so a failure always has one likely cause.

## Status

- [x] Phase 0 — bare FastAPI app + CI, deployed to Azure App Service
- [x] Phase 1 — Database models + complete `/jobs` CRUD API endpoints
- [ ] Phase 2 — Service Bus, producer side only (`POST /jobs` enqueues)
- [ ] Phase 3 — worker (Azure Function, consumes and processes)
- [ ] Phase 4 — Application Insights + structured logging

## API Reference (Phase 1)

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Liveness & database connection health check | `200 OK` |
| `GET` | `/` | Service info and current phase metadata | `200 OK` |
| `POST` | `/jobs` | Submit a new asynchronous job | `202 Accepted` |
| `GET` | `/jobs/{id}` | Get status, result, and lifecycle timestamps for a job | `200 OK` / `404` |
| `GET` | `/jobs` | List all jobs with pagination (`page`, `page_size`) and status filter (`status=pending`) | `200 OK` |
| `PATCH` | `/jobs/{id}/status` | Update job status, result, or error (worker hook) | `200 OK` / `404` |
| `DELETE` | `/jobs/{id}` | Cancel/delete a job record | `204 No Content` / `404` |

### Example Request: Create a Job

```bash
POST /jobs
Content-Type: application/json

{
  "task_type": "generate_report",
  "payload": {
    "year": 2026,
    "format": "pdf"
  }
}
```

Response:
```json
{
  "id": "caf8032e-56aa-44fa-aa3d-85bc645b9187",
  "task_type": "generate_report",
  "payload": {
    "year": 2026,
    "format": "pdf"
  },
  "status": "pending",
  "result": null,
  "error": null,
  "created_at": "2026-08-17T08:30:00Z",
  "updated_at": "2026-08-17T08:30:00Z"
}
```

## Local Development

```powershell
# 1. Activate venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Run tests
pytest -v

# 4. Start local server
uvicorn app.main:app --reload
```

- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
