# Job Queue & Status API

An asynchronous job-processing service. Built as a walking skeleton: each
phase adds exactly one new integration point and is deployed and verified
before the next one starts, so a failure always has one likely cause.

## Status

- [x] Phase 0 — bare FastAPI app + CI, deployed to Azure App Service
- [ ] Phase 1 — PostgreSQL + `/jobs` CRUD endpoints
- [ ] Phase 2 — Service Bus, producer side only (`POST /jobs` enqueues)
- [ ] Phase 3 — worker (Azure Function, consumes and processes)
- [ ] Phase 4 — Application Insights + structured logging

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/health` — should return `{"status": "ok"}`.

Run tests:

```bash
pytest -v
```

## Deploying Phase 0 to Azure App Service

You'll need an Azure account (Azure for Students gives $100 credit, no card
required) and the Azure CLI installed locally, or you can do all of this
through the Azure Portal instead.

### 1. Create the resources (CLI)

```bash
az login

az group create \
  --name job-queue-api-rg \
  --location centralindia

az appservice plan create \
  --name job-queue-api-plan \
  --resource-group job-queue-api-rg \
  --sku F1 \
  --is-linux

az webapp create \
  --name <pick-a-globally-unique-name> \
  --resource-group job-queue-api-rg \
  --plan job-queue-api-plan \
  --runtime "PYTHON:3.12"
```

`F1` is the free tier — fine for a demo project. It sleeps when idle and
has a daily CPU quota, so if you want it always warm for an interview demo,
switch to `B1` (a few dollars a month, covered by student credit).

### 2. Set the startup command

Azure can't auto-detect how to run a FastAPI app the way it does Flask/Django,
so this has to be set explicitly:

```bash
az webapp config set \
  --name <your-app-name> \
  --resource-group job-queue-api-rg \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0"
```

### 3. Connect GitHub Actions to Azure

Get the publish profile:

```bash
az webapp deployment list-publishing-profiles \
  --name <your-app-name> \
  --resource-group job-queue-api-rg \
  --xml
```

Copy the full XML output. In your GitHub repo: **Settings → Secrets and
variables → Actions → New repository secret**, name it
`AZURE_WEBAPP_PUBLISH_PROFILE`, and paste it in.

Then open `.github/workflows/ci-cd.yml` and replace
`CHANGE-ME-your-app-service-name` with your actual App Service name.

### 4. Push and watch it deploy

```bash
git add .
git commit -m "Phase 0: bare FastAPI skeleton with CI/CD"
git remote add origin <your-github-repo-url>
git push -u origin main
```

Watch the run under the **Actions** tab. Once it's green, hit
`https://<your-app-name>.azurewebsites.net/health` — if that returns
`{"status": "ok"}`, Phase 0 is done: deployment, CI, and hosting are all
proven to work before any business logic exists.

## Design notes

- No Docker in Phase 0 on purpose — App Service builds Python apps directly
  from `requirements.txt` via Oryx, so a container adds a moving part with
  nothing to show for it yet. It can be added later as a deliberate choice,
  not a requirement.
- `requirements.txt` and `requirements-dev.txt` are split so the production
  install stays minimal — pytest and httpx never ship to Azure.
