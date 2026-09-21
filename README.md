# Internal Request Intake & Triage Tool

A lightweight prototype for capturing messy internal requests, turning
them into a structured first-pass brief, and tracking triage status.
Built from scratch, Docker-native from the first commit, with every phase
verified against a running container before moving to the next.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** TypeScript, compiled with `tsc` to plain ES modules — no
  framework, no bundler
- **Brief generation:** Two interchangeable backends behind a common
  interface (`app/brief_generator.py`):
  - **Mock** (default): deterministic, keyword-free templated output, no
    network calls
  - **Groq** (optional, real model): used automatically when
    `GROQ_API_KEY` is set. Model confirmed via `GET /v1/models` against
    the live account before being hardcoded, not guessed from generic
    docs. Falls back to the mock automatically on any failure.

## Project layout

```
backend/
  app/
    main.py              FastAPI routes
    models.py             SQLAlchemy models (Request, Brief, AuditEntry)
    schemas.py             Pydantic request/response + brief output contract
    brief_generator.py    Mock + Groq generators, swappable interface
    duplicates.py           Duplicate-request detection
    auth.py                  Reviewer-token auth
    webhooks.py               Accepted-request webhook stub
    eval_briefs.py         Brief-quality eval script
    database.py
    tests/
      conftest.py           Shared test DB/TestClient fixtures
      test_api.py          Core API tests
      test_stretch.py       Duplicate detection, auth, webhook tests
  Dockerfile
  requirements.txt
frontend/
  src/
    app.ts               App logic: submit/queue/detail views
  index.html
  tsconfig.json
  package.json
  Dockerfile
docker-compose.yml
```

## Run with Docker (recommended)

```bash
cp .env.example .env    # optional: fill in GROQ_API_KEY / REVIEWER_TOKEN / WEBHOOK_URL
docker compose up --build
```

- Frontend: http://localhost:5500
- Backend / API docs: http://localhost:8000/docs

```bash
docker compose down -v   # stop and wipe the SQLite volume
```

Run tests inside the container:
```bash
docker compose run --rm backend pytest app/tests/ -v
```

## Run without Docker

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npx tsc
python3 -m http.server 5500
```

## Test

```bash
docker compose run --rm backend pytest app/tests/ -v
```

11 tests: core CRUD/validation/triage/audit (6) plus duplicate detection,
reviewer auth, webhook firing, and CSV export (5).

```bash
docker compose run --rm backend python -m app.eval_briefs
```

## Optional configuration

| Variable         | Effect |
|------------------|--------|
| `GROQ_API_KEY`   | Switches brief generation from mock to Groq. |
| `REVIEWER_TOKEN` | Gates queue/detail/triage-update/audit behind `X-Reviewer-Token`. Submission stays open. Unset = open. |
| `WEBHOOK_URL`    | POSTs a JSON payload when a request is marked `accepted`. Failures are logged, never break the triage update. |

## API routes

| Method | Path                        | Auth (if `REVIEWER_TOKEN` set) | Purpose |
|--------|-----------------------------|---------------------------------|---------|
| POST   | `/requests`                 | Open                            | Submit; generates brief; flags duplicates |
| GET    | `/requests`                 | Reviewer                        | List/filter |
| GET    | `/requests/{id}`            | Reviewer                        | Detail |
| PATCH  | `/requests/{id}`            | Reviewer                        | Triage update; fires webhook on accept |
| GET    | `/requests/{id}/audit`      | Reviewer                        | Audit trail |
| GET    | `/requests/export/csv`      | Open                            | CSV export |

## Assumptions

- SQLite is sufficient for a prototype; not for concurrent production load
  or Render's ephemeral filesystem without a persistent disk attached.
- Reviewer auth is a single shared token, not per-user accounts.
- Duplicate detection is lexical (`difflib`), not semantic.
- The mock generator is intentionally simple; its output still conforms
  exactly to the schema a real model must produce, so swapping generators
  is a one-class change.

## Known gaps

- No pagination on `/requests`.
- No per-user accounts.
- No durable webhook delivery (no retry/queue).
- CSV export is deliberately left open even when `REVIEWER_TOKEN` is set,
  since the frontend serves it as a plain link that can't attach a custom
  header.

## Stretch goals implemented

All six: CSV export, audit history, evaluation script, Docker/Compose,
duplicate-request detection, requester/reviewer auth, and a webhook stub.
