# MASTER HANDOVER — Job Queue & Status API

**Last updated:** 2026-08-17
**Repo:** https://github.com/Samarthh1010101010/job-queue-api
**Azure resource:** App Service `samarth-job-api-2026` in resource group `job-queue-api-rg`

This is the single source of truth. Read Section 1 before touching anything else.

---

## 1. How much to build — read before writing any code

The #1 risk is not "too little project." It's building something that can't be
explained. A previous agent session on a different project silently added an
unrequested LRU + "ML" eviction feature and mislabeled a hand-tuned heuristic as
machine learning. That must not happen again.

Rules for any agent or person working on this:

- **Every shipped feature must be explainable unprompted** — what it does, why it's
  built that way, what happens when it fails. If it can't be explained without
  notes, it does not go on the resume, even if the code works.
- **Do not expand scope silently.** No "while I'm at it" extras, no
  cleverer-than-asked implementations, no swapping a simple approach for an
  impressive one without asking first.
- **Build depth ceiling:** Phase 1 confidently. Phase 2 only if it goes cleanly.
  Phases 3–4 are out of scope. This is a ceiling, not a target.
- **When unsure whether something is too much, leave it out and ask.**
- **Every number** used in code, resume, or conversation must come from a run that
  was actually executed and can be shown. Never estimated, inferred, or written up
  unrun.
- **Never mark a phase "done" without hitting the live URL and confirming the
  response.** Passing local tests is necessary, not sufficient.

---

## 2. Project context

A real, deployed async job-processing API, built to support a resume for
**Microsoft Software Engineering Intern, Job 200041085** (university internship
pool — *not* 200047364, a full-time role already ruled out on eligibility).
Self-imposed 2-day build budget.

---

## 3. Verified state as of 2026-08-17

Everything in this section was directly observed, not inferred.

### Works

- **Code for Phases 0, 1, and 2 all exists and is committed.** A prior session built
  further than expected. `app/` contains `main.py`, `config.py`, `db.py`, `crud.py`,
  `models.py`, `schemas.py`, `queue.py`, `routers/jobs.py`.
- **Git is clean.** 13 commits, `main` only, local matches `origin/main`. No secrets
  or venv tracked. `.gitignore` correctly excludes `.env` and `venv/`.
- **CI is green.** Run #12 (commit `929d2f7`) succeeded — both `Test & Lint` and
  `Build & Deploy to Azure App Service`. The Azure publish profile secret works and
  the deploy action delivers the package.
- **Tests pass in CI** against a Postgres 16 service container.
- **Azure startup command is correctly set** to `bash startup.sh`.

### Broken

- **The deployed app does not serve.** `/health`, `/`, and `/docs` all return empty
  bodies. Deploy succeeding is not the same as the app starting.
- **`DATABASE_URL` is not set in Azure.** App settings contained only
  `SCM_DO_BUILD_DURING_DEPLOYMENT`. The app therefore falls back to the hardcoded
  default in `config.py` (`postgresql://postgres:postgres@localhost:5432/postgres`),
  pointing at a Postgres that does not exist inside the App Service container.
- **`SCM_DO_BUILD_DURING_DEPLOYMENT` was misconfigured** — it held a non-boolean
  string (a password had been pasted into the field). Azure reads anything that
  isn't `true` as false, so Oryx skipped dependency installation entirely.
  *That password should be treated as exposed and rotated wherever it was used.*
- **No Neon database exists yet.** No `.env` on disk, so local development cannot
  run either. This blocks everything else.

### Unverified — do not claim

- **Phase 2 (Azure Service Bus) has never sent a message to a real queue.** All
  three tests in `tests/test_queue.py` mock `ServiceBusClient` entirely.
  `SERVICE_BUS_CONNECTION_STRING` is referenced only in `config.py` (empty default)
  and `queue.py`. It is set nowhere in CI, nowhere in Azure. `send_job_message`
  therefore returns `False` on every `POST /jobs` in production, silently, by
  design. **The README currently marks Phase 2 as done. That claim is not
  supported.**
- **The `/jobs` endpoints have never been confirmed working against a live
  deployment** — only against CI's throwaway Postgres container.

### Changed in this session (2026-08-17)

The `.python_packages` mechanism was removed in three places, because setting
`SCM_DO_BUILD_DURING_DEPLOYMENT=true` makes Azure install `requirements.txt`
normally and renders it redundant:

1. `.github/workflows/ci-cd.yml` — dropped the
   `pip install -r requirements.txt --target=".python_packages/lib/site-packages"` step
2. `startup.sh` — dropped the `PYTHONPATH` export
3. `app/main.py` — dropped the `sys.path` shim

Verified after the change: `app/main.py` parses, no `python_packages` references
remain anywhere in the repo, and the 4 non-database tests still pass.

*Known wart:* the deploy job still has a `Set up Python` step that no longer
installs anything. Harmless, but dead. Remove it if you want a cleaner story.

---

## 4. Next steps, in order

1. **Create the Neon database.** Two databases — one dev, one prod — so local
   testing never touches live data. Neon replaces both Docker and a local Postgres
   install. Copy the prod connection string.
2. **Set `DATABASE_URL`** in Azure → Settings → Environment variables → App settings.
3. **Set `SCM_DO_BUILD_DURING_DEPLOYMENT` to `true`.**
4. **Enable application logging** — Monitoring → App Service logs → Application
   logging (Filesystem) = On, level Verbose. Then use **Log stream**, not the
   Activity Log. The Activity Log only shows control-plane operations (deploys,
   config edits, restarts) and cannot explain a boot failure.
5. **Push to trigger CI**, then hit the live `/health`. Success looks like
   `{"status":"ok","phase":2,"database":"connected"}`. Anything else — read the log
   stream.
6. **Verify all four `/jobs` endpoints against the live URL**, not just CI.
7. **Decide Phase 2:** either provision a real Service Bus namespace and confirm a
   message actually lands in the queue, or remove the claim from the README and
   keep it off the resume.
8. **Correct the README** so it describes only what is verified live.
9. **Stop.** No Phase 3 (worker), no Phase 4 (Application Insights).

---

## 5. Known repo untidiness

- The repo is nested awkwardly: `job-queue-status-api/job-queue-api-phase0/job-queue-api/`.
  The git repo is the innermost folder.
- A stray `venv/` and `.pytest_cache/` sit in the outer Desktop folder, outside the
  repo. Untracked and harmless, but confusing.
- **`render.yaml` is dead config.** It targets Render with a normal pip install and
  a gunicorn start command, contradicting the Azure path entirely, and is wired to
  nothing. Delete it or commit to it — do not leave both.

---

## 6. Resume rules

- Target title: **"Software Engineering Intern"** (this posting's actual title), not
  "Software Engineer."
- Job Queue bullets describe **only what is actually deployed and verified** at the
  time the resume is finalized — not the full phase vision.
- **Mini Redis:** use the plain original version (SET/GET/DEL, hash table). Not the
  cache/eviction/"ML" variant from an earlier unverified session — that isn't
  understood well enough to defend.
- **Leave out:** TBIE (solo-vs-team status never resolved), Kubernetes (no real
  experience), "Redis" as a listed skill (Mini Redis is a clone, not Redis usage),
  "LLMs & Agentic AI" (not backed by anything built).
- **Keep as-is:** XelerAIT experience bullets, Continual Learning Recommender
  project, C++ in the Languages line.
- Replace any `[Phone]` / `[Email]` placeholders with real contact info.
- Final format: one page, PDF, clean filename (not "DRAFT").

## 7. LinkedIn

- Experience and projects must mirror the final resume exactly — recruiters
  cross-check.
- Headline reflects the target role (Software Engineering Intern).
- Dates and descriptions match the resume, not a fuller or older version.

## 8. Application — Job 200041085

- **Required:** currently pursuing a Bachelor's/Master's in CS or related; at least
  1 semester/term remaining after the internship ends; 1 year of OOP experience.
- **Preferred:** CS fundamentals (data structures & algorithms).
- General pool posting — no specific stack required. The project is a
  differentiator, not a keyword match.
- **Open item, confirm before submitting:** that the actual internship dates leave
  ≥1 semester remaining given a 2023–2027 B.Tech program.
- Steps: create/sign in to profile, upload final PDF, answer screening questions
  carefully — especially graduation date and eligibility.

---

## 9. Final checklist

1. [ ] Neon created, `DATABASE_URL` set, app boots, `/health` verified live
2. [ ] All four `/jobs` endpoints verified against the live URL
3. [ ] Phase 2 resolved — verified for real, or claim removed
4. [ ] README accurate to what is actually deployed
5. [ ] Resume bullets rewritten to match verified state
6. [ ] Real contact info filled in, exported as PDF
7. [ ] ATS check (e.g. Jobscan) against job 200041085
8. [ ] LinkedIn synced to final resume
9. [ ] Repo pushed and pinned on GitHub
10. [ ] ≥1-semester eligibility confirmed
11. [ ] Submitted via Microsoft Careers portal
