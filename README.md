# DataPump

DataPump is a data ingestion pipeline: a service that takes in data (starting with CSV, eventually JSON and other formats), processes/transforms it, and lands it somewhere useful — a PostgreSQL database, a cleaned dataset, or an input ready for an ML model. It's built with **FastAPI** on top of **PostgreSQL** (via raw SQL, no ORM).

This isn't meant to be production-grade, but it's a real, working project rather than a disposable exercise — something built with care, meant to actually work end-to-end and be worth showing. The exact shape of the "pump" (transformation/processing) step is still being worked out; right now the focus is on getting the foundations (API, database schema, job tracking, error handling) solid first.

> This is a work-in-progress. Expect things to change as the design evolves.

## Current status

The job layer is backed by real PostgreSQL, and the database schema is now versioned in the repo: a migration script creates the `jobs` table (with constraints and an index) and a seed script fills it with realistic random data for testing. You can create and list jobs through the API, with hand-written SQL, async connection pooling, and database errors translated into proper HTTP responses.

Working:
- FastAPI app with a lifespan hook that opens/closes an async PostgreSQL connection pool on startup/shutdown
- `GET /`, `GET /health`, and `GET /check-db-conn` (verifies the API can reach the database)
- `POST /jobs` — creates a job row (`INSERT ... RETURNING`) and returns it
- `GET /jobs` — returns all jobs (`SELECT * FROM jobs`)
- A `get_db_conn` FastAPI dependency that hands each request a pooled connection
- A migration script that creates the `job_status` enum, the `jobs` table with integrity checks, and an index
- A seed script that inserts N randomly generated, constraint-valid jobs
- A custom database exception hierarchy, mapped to HTTP status codes by a global exception handler
- Pydantic schemas for jobs (`JobCreate`, `JobUpdate`, `JobResponse`, `JobStatus`) with input validation

Not yet built:
- `GET /jobs/{id}` and `PATCH /jobs/{id}` (`JobUpdate` is defined but not used by any endpoint yet)
- Actual reading/parsing of CSV or JSON data
- The "pump" step — whatever transformation/processing turns raw input into something useful
- A background worker that actually runs jobs (right now jobs are only recorded, never executed)
- Pagination/filtering on `GET /jobs` (it returns every row, which matters once you've seeded a lot of data)
- Auth, tests

## Tech stack

- **FastAPI** — web framework / API layer
- **Pydantic** — data validation and schemas
- **Uvicorn** — ASGI server
- **PostgreSQL** — persistence layer (uses `gen_random_uuid()`, so PostgreSQL 13+)
- **psycopg** (async) + **psycopg-pool** — raw SQL, no ORM
- **python-dotenv** — loads DB credentials from `.env`
- **Python 3.11+** (uses `X | None` type syntax)

## Project structure

```
DataPump/
├── api/
│   ├── main.py                  # FastAPI app, DB-connection dependency, all endpoints
│   ├── models.py                # Pydantic schemas (JobCreate, JobUpdate, JobResponse, JobStatus)
│   ├── exceptions.py            # Global handler: DatabaseError -> HTTP status code + JSON message
│   ├── handler/
│   │   ├── post_jobs.py         # SQL + error translation for creating a job
│   │   └── get_jobs.py          # SQL + error translation for listing jobs
│   └── __init__.py              # Re-exports schemas from models.py
├── datapump/
│   ├── database/
│   │   └── connection.py        # Async PostgreSQL connection pool + lifespan (psycopg + psycopg-pool)
│   ├── migration/
│   │   └── migrate.py           # Creates the job_status enum, jobs table, and index
│   ├── seed/
│   │   └── plant_seeds.py       # Inserts N random, constraint-valid jobs for testing
│   ├── exceptions/
│   │   └── db_exceptions.py     # DatabaseError and subclasses
│   ├── app/                     # Reserved for application/business logic (empty for now)
│   └── __init__.py              # Re-exports db_pool, conn_pool_lifespan, and the database exceptions
├── .env.example                 # Template for required DB env vars
├── license                      # MIT license text
├── pyproject.toml
└── README.md
```

### How a request flows

```
HTTP request
  └─ api/main.py              route + get_db_conn dependency (borrows a connection from the pool)
       └─ api/handler/*.py    runs the raw SQL, catches psycopg errors, re-raises as DatabaseError subclasses
            └─ api/exceptions.py   turns any DatabaseError into a JSON response with the right status code
```

### Database connection

`datapump/database/connection.py` sets up an `AsyncConnectionPool` (from `psycopg_pool`) using credentials read from environment variables via `python-dotenv`. Pool settings: `min_size=1`, `max_size=10`, `timeout=5` seconds, rows returned as dicts (`dict_row`). The pool is opened on app startup (and waits until it's ready) and closed on shutdown via a FastAPI `lifespan` context manager (`conn_pool_lifespan`), so the pool's lifetime is tied to the app's.

Persistence is plain **PostgreSQL via psycopg, raw SQL, no ORM** — no SQLAlchemy/SQLModel. Queries are written by hand in `api/handler/`.

## Environment setup

Copy `.env.example` to `.env` and fill in your local Postgres credentials:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

A running PostgreSQL instance (with the database in `DB_NAME` already created) is required, since the connection pool opens on startup and the migration needs somewhere to create the table.

## Database schema

`datapump/migration/migrate.py` creates everything the API needs. It is safe to re-run: the enum is created inside a `DO` block that ignores `duplicate_object`, and the table and index use `IF NOT EXISTS`.

**Enum:** `job_status` = `'pending' | 'processing' | 'completed' | 'failed'`

**Table `jobs`:**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key, defaults to `gen_random_uuid()` |
| `job_source` | `VARCHAR(100)` | `NOT NULL`, must not be blank |
| `destination` | `VARCHAR(100)` | `NOT NULL`, must not be blank |
| `batch_size` | `INT` | `NOT NULL`, default `1000`, must be 1–10,000 |
| `status` | `job_status` | `NOT NULL`, default `'pending'` |
| `total_records` | `INT` | `NOT NULL`, default `0`, must be ≥ 0 |
| `processed_records` | `INT` | `NOT NULL`, default `0`, must be ≥ 0 and ≤ `total_records` |
| `error_message` | `TEXT` | Nullable |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, defaults to `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMPTZ` | Nullable |
| `completed_at` | `TIMESTAMPTZ` | Nullable |

**Index:** `idx_status_created_at` on `(status, created_at)`.

**Status consistency rules.** A `validate_job_status` check constraint makes the database reject rows whose fields don't agree with their status:

| `status` | `processed_records` | `updated_at` | `completed_at` | `error_message` |
|---|---|---|---|---|
| `pending` | `= 0` | any | `NULL` | `NULL` |
| `processing` | `< total_records` | not `NULL` | `NULL` | `NULL` |
| `completed` | `= total_records` | not `NULL` | not `NULL` | `NULL` |
| `failed` | `< total_records` | not `NULL` | `NULL` | not `NULL` and not blank |

This is worth keeping in mind for the future `PATCH /jobs/{id}` endpoint and the background worker: any status change has to update the related columns in the same statement, or Postgres will raise an integrity error (returned as a `409`).

Two limits are enforced by the database but not by the Pydantic models: `job_source` / `destination` are capped at 100 characters, so a longer value passes request validation and then fails in Postgres (surfaced as a `422` `DatabaseDataError`).

## Running the migration and seed scripts

Run both from the repository root, after `.env` is filled in:

```bash
# 1. create the enum, table and index
python -m datapump.migration.migrate

# 2. (optional) insert random test data — prompts for how many rows
python -m datapump.seed.plant_seeds
```

The seed script asks `Enter the no. of rows to plant the seed data:` and generates that many jobs with random sources/destinations (e.g. `postgres://db/source1`, `api://dest_endpoint2`), a random status, record counts up to 100,000, and values for `processed_records`, `error_message`, `updated_at`, and `completed_at` that satisfy the status rules above. Some things to know:

- It **appends** rows — running it again adds more rather than resetting the table.
- `created_at` is generated as "now + up to 40 days", so seeded jobs have timestamps in the future.
- Input must be a whole number; anything else crashes with a `ValueError`.
- Rows are generated randomly, so very rarely (a job with `total_records = 0` in the `processing`/`failed` state) a row can violate the status constraint and the insert will fail with a `DatabaseUnexpectedError`; just re-run it.

## The Job model

Defined in `api/models.py`, representing one unit of work: take data from a `job_source`, process it in batches, and send it to a `destination`.

**`JobCreate`** (request body for `POST /jobs`):

| Field | Type | Description |
|---|---|---|
| `job_source` | str | Source of the data (required) |
| `destination` | str | Destination table of the database (required) |
| `batch_size` | int | Records processed per batch (1–10,000, default 1000) |

`job_source` and `destination` are stripped of surrounding whitespace, and empty/whitespace-only values are rejected.

**`JobResponse`** (returned by the job endpoints):

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique job identifier |
| `job_source` | str | Where the input data comes from |
| `destination` | str | Where the processed data should go |
| `batch_size` | int | Records processed per batch |
| `status` | enum | `pending`, `processing`, `completed`, `failed` |
| `processed_records` | int | Records processed so far |
| `total_records` | int | Total records to process |
| `error_message` | str \| None | Populated if the job fails |
| `created_at` | datetime | When the job was created |
| `updated_at` / `completed_at` | datetime \| None | Set as the job progresses |

**`JobUpdate`** (all fields optional: `status`, `processed_records`, `total_records`, `error_message`) is intended for a future background worker to report progress. It isn't used by any endpoint yet.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Welcome message / project description |
| `GET` | `/health` | Health check |
| `GET` | `/check-db-conn` | Confirms the API can reach the PostgreSQL database |
| `POST` | `/jobs` | Create a job. Body: `JobCreate`. Returns `JobResponse` |
| `GET` | `/jobs` | List all jobs. Returns `list[JobResponse]` |

Example:

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_source": "data/users.csv", "destination": "users", "batch_size": 500}'

curl http://127.0.0.1:8000/jobs
```

New jobs always start as `pending` with `0` processed and `0` total records.

## Error handling

Database failures are caught in the handlers, re-raised as `DatabaseError` subclasses (exported from `datapump`), and converted to JSON responses of the form `{"message": "..."}` by the global handler in `api/exceptions.py`:

| Exception | HTTP status | Raised when |
|---|---|---|
| `DatabaseConnectionPoolTimeout` | 408 | No pooled connection became available within the pool timeout |
| `DatabaseConnectionPoolClosed` | 503 | The pool is closed (e.g. during shutdown) |
| `DatabaseDataError` | 422 | Postgres rejects the data (`psycopg.DataError`), e.g. a value longer than 100 characters |
| `DatabaseIntegrityError` | 409 | A constraint is violated (`psycopg.IntegrityError`) |
| `DatabaseProgrammingError` | 500 | Bad SQL or a missing table/column (`psycopg.ProgrammingError`), e.g. the migration hasn't been run |
| `DatabaseUnexpectedError` | 500 | Any other `psycopg.Error` |

Request-body validation errors (e.g. `batch_size` out of range, blank `job_source`) are handled by FastAPI/Pydantic and return the standard 422 response.

## Getting started

```bash
# clone the repo
git clone https://github.com/utsabkhadka0710/DataPump.git
cd DataPump

# install dependencies
pip install -e .

# set up environment variables
cp .env.example .env
# then fill in DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# create the jobs table, then optionally seed it
python -m datapump.migration.migrate
python -m datapump.seed.plant_seeds

# run the API (requires Postgres running and reachable)
fastapi dev api/main.py
```

Once running, interactive docs are available at `http://127.0.0.1:8000/docs`.

## Roadmap

Roughly the order things are expected to get built, though this may shift:

- [x] Connect to PostgreSQL with an async connection pool (raw SQL via psycopg)
- [x] `POST /jobs` and `GET /jobs` backed by real SQL
- [x] Map database errors to HTTP responses
- [x] Design the `jobs` table schema and commit it as a migration
- [x] Seed script for generating test data
- [ ] `GET /jobs/{id}`
- [ ] Wire up `JobUpdate` to a `PATCH /jobs/{id}` endpoint so job status/progress can actually change
- [ ] Pagination/filtering for `GET /jobs`
- [ ] Add CSV ingestion + parsing
- [ ] Define what "pumping" actually means — cleaning, validation, transformation, feature extraction for ML, etc.
- [ ] Add a background worker (FastAPI `BackgroundTasks` or a proper queue like Celery/RQ) to actually execute jobs instead of only tracking their state
- [ ] JSON ingestion support
- [ ] Basic tests (pytest)

## Why this project exists

DataPump exists to be a real, working data ingestion pipeline: take raw files in, process them, and get something usable out the other end — reliably, and in a way that's actually worth putting in front of other people. It's not aimed at production scale, but it's being built properly: a real API, real async PostgreSQL access with raw SQL, real job tracking, and (eventually) real background processing — not a disposable toy project.

## License

MIT — see [license](license) for details.