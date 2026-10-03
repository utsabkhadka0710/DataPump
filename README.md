# DataPump

DataPump is a data ingestion pipeline: a service that takes in data (starting with CSV, eventually JSON and other formats), processes/transforms it, and lands it somewhere useful — a PostgreSQL database, a cleaned dataset, or an input ready for an ML model. It's built with **FastAPI** on top of **PostgreSQL** (via raw SQL, no ORM).

This isn't meant to be production-grade, but it's a real, working project rather than a disposable exercise — something built with care, meant to actually work end-to-end and be worth showing. The exact shape of the "pump" (transformation/processing) step is still being worked out; right now the focus is on getting the foundations (API skeleton, database connectivity, job tracking) solid first.

> This is a work-in-progress. Expect things to change as the design evolves.

## Current status

The project just moved from an in-memory placeholder store to real **PostgreSQL** connectivity. As part of that shift, the job endpoints that existed earlier (create/list/get jobs backed by an in-memory `FakeDb`) have been pulled out for now while the database layer is built properly — so right now the API itself is minimal.

Working:
- FastAPI app with a lifespan hook that opens/closes an async PostgreSQL connection pool on startup/shutdown
- `/health` and `/` endpoints
- `/check-db-conn` endpoint to verify the API can actually reach the database
- Pydantic schemas for jobs (`JobCreate`, `JobUpdate`, `JobResponse`, `JobStatus`) defined in `api/models.py`, ready to be wired up once the DB layer is in place

Not yet built:
- Any job endpoints (`POST`/`GET`/`PATCH /jobs`) — removed along with `FakeDb`, to be reintroduced backed by real SQL
- Actual reading/parsing of CSV or JSON data
- The "pump" step — whatever transformation/processing turns raw input into something useful
- SQL queries/table schema for jobs (connection pool exists, but nothing queries real tables yet)
- A background worker that actually runs jobs
- Auth, config management, tests

## Tech stack

- **FastAPI** — web framework / API layer
- **Pydantic** — data validation and schemas
- **Uvicorn** — ASGI server
- **PostgreSQL** — persistence layer
- **psycopg** (async) + **psycopg-pool** — raw SQL, no ORM
- **python-dotenv** — loads DB credentials from `.env`
- **Python 3.11+** (uses `X | None` type syntax)

## Project structure

```
DataPump/
├── api/
│   ├── main.py                  # FastAPI app, lifespan, health/db-check endpoints
│   ├── models.py                # Pydantic schemas (JobCreate, JobUpdate, JobResponse, JobStatus)
│   └── __init__.py              # Re-exports schemas from models.py
├── datapump/
│   ├── database/
│   │   └── connection.py        # Async PostgreSQL connection pool (psycopg + psycopg-pool)
│   ├── app/                     # Reserved for application/business logic (empty for now)
│   └── __init__.py              # Re-exports db_pool, conn_pool_lifespan
├── .env.example                 # Template for required DB env vars
├── pyproject.toml
└── README.md
```

### Database connection

`datapump/database/connection.py` sets up an `AsyncConnectionPool` (from `psycopg_pool`) using credentials read from environment variables via `python-dotenv`, with rows returned as dicts (`dict_row`). The pool is opened on app startup and closed on shutdown via a FastAPI `lifespan` context manager (`conn_pool_lifespan`), so the pool's lifetime is tied to the app's.

Persistence is plain **PostgreSQL via psycopg, raw SQL, no ORM** — no SQLAlchemy/SQLModel. Queries will be written by hand as the job endpoints get rebuilt on top of this.

## Environment setup

Copy `.env.example` to `.env` and fill in your local Postgres credentials:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

A running PostgreSQL instance is required to start the app, since the connection pool opens on startup.

## The Job model (schemas, not yet wired to endpoints)

Defined in `api/models.py`, representing one unit of work: take data from a `source`, process it in batches, and send it to a `destination`. Not yet connected to any endpoint or table.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique job identifier |
| `source` | str | Where the input data comes from |
| `destination` | str | Where the processed data should go |
| `batch_size` | int | Records processed per batch (1–10,000, default 1000) |
| `status` | enum | `pending`, `processing`, `completed`, `failed` |
| `processed_records` | int | Records processed so far |
| `total_records` | int | Total records to process |
| `error_message` | str \| None | Populated if the job fails |
| `created_at` / `updated_at` / `completed_at` | datetime | Timestamps |

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Welcome message / project description |
| `GET` | `/health` | Health check |
| `GET` | `/check-db-conn` | Confirms the API can reach the PostgreSQL database |

Job endpoints (`/jobs`) are not currently present — they'll come back once they're backed by real SQL against Postgres.

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

# run the API (requires Postgres running and reachable)
fastapi dev api/main.py
```

Once running, interactive docs are available at `http://127.0.0.1:8000/docs`.

## Roadmap

Roughly the order things are expected to get built, though this may shift:

- [ ] Design the `jobs` table schema in Postgres
- [ ] Rebuild `POST /jobs`, `GET /jobs`, `GET /jobs/{id}` on top of raw SQL via psycopg (replacing the old `FakeDb`-backed versions)
- [ ] Wire up `JobUpdate` to a `PATCH /jobs/{id}` endpoint so job status/progress can actually change
- [ ] Add CSV ingestion + parsing
- [ ] Define what "pumping" actually means — cleaning, validation, transformation, feature extraction for ML, etc.
- [ ] Add a background worker (FastAPI `BackgroundTasks` or a proper queue like Celery/RQ) to actually execute jobs instead of only tracking their state
- [ ] JSON ingestion support
- [ ] Basic tests (pytest)

## Why this project exists

DataPump exists to be a real, working data ingestion pipeline: take raw files in, process them, and get something usable out the other end — reliably, and in a way that's actually worth putting in front of other people. It's not aimed at production scale, but it's being built properly: a real API, real async PostgreSQL access with raw SQL, real job tracking, and (eventually) real background processing — not a disposable toy project.

## License

MIT