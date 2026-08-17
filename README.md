# Job Queue & Status API

An asynchronous job-processing service built as a walking skeleton: each
phase adds exactly one new integration point, deployed and verified
with continuous integration.

## Architecture & Features

- **Framework**: FastAPI (async ASGI)
- **Database Layer**: Direct PostgreSQL with `asyncpg` connection pooling and native JSONB serialization
- **Message Broker**: Azure Service Bus (Producer side with asynchronous dispatch and resilient fallback)
- **CI/CD**: GitHub Actions pipeline running automated test suite against PostgreSQL 16 container, deploying to Azure App Service
- **Hosting**: Azure Linux App Service (`samarth-job-api-2026`)

## Roadmap & Status

- [x] **Phase 0** — bare FastAPI app + CI, deployed to Azure App Service
- [x] **Phase 1** — Database layer (`asyncpg` + PostgreSQL) + full `/jobs` CRUD API
- [x] **Phase 2** — Azure Service Bus integration (`POST /jobs` enqueues to `jobs` queue)
- [ ] **Phase 3** — Worker (Azure Function or background consumer)
- [ ] **Phase 4** — Application Insights + structured JSON logging

---

## API Reference

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Liveness & database connection health check | `200 OK` / `503` |
| `GET` | `/` | Service info and active phase metadata | `200 OK` |
| `POST` | `/jobs` | Submit a new job (saves to DB with `queued` status, dispatches to Service Bus) | `202 Accepted` |
| `GET` | `/jobs/{id}` | Retrieve status, results, and timestamps for a specific job ID | `200 OK` / `404` |
| `GET` | `/jobs` | List jobs with optional status filter (`?status=queued`) and limit (`?limit=20`) | `200 OK` |
| `DELETE` | `/jobs/{id}` | Cancel a queued job (returns `409 Conflict` if already processing/completed) | `200 OK` / `404` / `409` |

---

### Example Requests & Responses

#### 1. Submit a Job (`POST /jobs`)
```http
POST /jobs
Content-Type: application/json

{
  "job_type": "generate_report",
  "target": "Q3-2026-revenue",
  "metadata": {
    "format": "pdf",
    "fiscal_year": 2026
  }
}
```

Response (`HTTP 202 Accepted`):
```json
{
  "id": "7d9b9356-4299-4c8d-8fb0-b74a065bc7c5",
  "job_type": "generate_report",
  "target": "Q3-2026-revenue",
  "metadata": {
    "format": "pdf",
    "fiscal_year": 2026
  },
  "status": "queued",
  "result": null,
  "error_message": null,
  "created_at": "2026-08-17T07:30:00Z",
  "updated_at": "2026-08-17T07:30:00Z"
}
```

#### 2. Cancel a Queued Job (`DELETE /jobs/{id}`)
```http
DELETE /jobs/7d9b9356-4299-4c8d-8fb0-b74a065bc7c5
```

Response on success (`HTTP 200 OK`):
```json
{
  "id": "7d9b9356-4299-4c8d-8fb0-b74a065bc7c5",
  "job_type": "generate_report",
  "target": "Q3-2026-revenue",
  "metadata": {
    "format": "pdf",
    "fiscal_year": 2026
  },
  "status": "cancelled",
  "result": null,
  "error_message": null,
  "created_at": "2026-08-17T07:30:00Z",
  "updated_at": "2026-08-17T07:32:10Z"
}
```

Response on attempting to cancel a non-queued job (`HTTP 409 Conflict`):
```json
{
  "detail": "Job can only be cancelled when in 'queued' status. Current status: 'cancelled'."
}
```

---

## Local Setup & Configuration

1. **Environment Configuration (`.env`)**:
   ```env
   DATABASE_URL=postgresql://neondb_owner:password@ep-sample.centralindia.aws.neon.tech/neondb?sslmode=require
   SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://sample.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=...
   ```

2. **Run Tests**:
   ```bash
   pytest -v
   ```

3. **Start Local Development Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
