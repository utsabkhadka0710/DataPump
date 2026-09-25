# DataPump

DataPump is a learning project built to get hands-on with **FastAPI** by building something close to a real-world backend service: a data processing job API.

The core idea is a service that takes in data (starting with CSV, eventually JSON and other formats), "pumps" it through some transformation/processing pipeline, and lands it somewhere useful — a database table, a cleaned dataset, or an input ready for an ML model. The exact shape of the pumping/transformation logic is still being figured out; right now the project focuses on getting the job-management API right first.

> This is a work-in-progress, built for learning purposes. Expect things to change quickly and roughly as the design evolves.

## Current status

What exists today is the **job tracking API** — the part of the system responsible for creating and looking up data-processing jobs. There is no actual CSV/data processing pipeline yet, and no persistent database; jobs are currently stored in memory via a small `FakeDb` class as a stand-in.

Working:
- Health check and root endpoints
- Create a job with a source, destination, and batch size
- List all jobs
- Fetch a single job by ID

Not yet built:
- Updating a job's status/progress (a `JobUpdate` schema already exists in `models.py` but isn't wired to any endpoint yet — no `PATCH` route currently)
- Actual reading/parsing of CSV or JSON data
- The "pump" step — whatever transformation/processing turns raw input into something useful
- A real database layer (Postgres, SQLite, etc. — currently just an in-memory `dict` inside `FakeDb`)
- A background worker that actually runs jobs
- Auth, config management, tests

## Tech stack

- **FastAPI** — web framework / API layer
- **Pydantic** — data validation and schemas
- **Uvicorn** — ASGI server
- **Python 3.11+** (uses `X | None` type syntax)

## Project structure

```
DataPump/
├── api/
│   ├── main.py          # FastAPI app, FakeDb store, and job endpoints
│   ├── models.py        # Pydantic schemas (JobCreate, JobUpdate, JobResponse, JobStatus)
│   └── __init__.py      # Re-exports schemas from models.py
├── app/                 # Reserved for application/business logic (empty for now)
├── database/            # Reserved for the real database layer (empty for now)
├── pyproject.toml
└── README.md
```

### `FakeDb`

Jobs are currently held in memory by a small `FakeDb` class in `main.py` (a dict under the hood, keyed by `"job {id}"`). It exists purely as a placeholder until a real database layer is built under `database/`.

## The Job model

A `Job` represents one unit of work: take data from a `source`, process it in batches, and send it to a `destination`.

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
| `POST` | `/jobs` | Create a new job |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Get a single job by ID |

There's no `PATCH /jobs/{id}` yet, so job status/progress can't be updated through the API — jobs are created as `pending` and stay that way until the worker/update logic is built.

## Getting started

```bash
# clone the repo
git clone https://github.com/utsabkhadka0710/DataPump.git
cd DataPump

# install dependencies
pip install -e .

# run the API
fastapi dev api/main.py
```

Once running, interactive docs are available at `http://127.0.0.1:8000/docs`.

### Example: create a job

```bash
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source": "data/input.csv",
    "destination": "processed_records",
    "batch_size": 500
  }'
```

## Roadmap

Roughly the order things are expected to get built, though this may shift:

- [ ] Wire up `JobUpdate` to a `PATCH /jobs/{id}` endpoint so job status/progress can actually change
- [ ] Add a real persistence layer under `database/` (likely SQLite/Postgres via SQLAlchemy or SQLModel), replacing `FakeDb`
- [ ] Add CSV ingestion + parsing
- [ ] Define what "pumping" actually means — cleaning, validation, transformation, feature extraction for ML, etc.
- [ ] Add a background worker (FastAPI `BackgroundTasks` or a proper queue like Celery/RQ) to actually execute jobs instead of only tracking their state
- [ ] JSON ingestion support
- [ ] Basic tests (pytest)
- [ ] Config/env handling

## Why this project exists

This is primarily a sandbox for learning FastAPI patterns — request/response models with Pydantic, status codes, path/body validation, and structuring a project that can grow into something with real background processing and a real database. The "data pump" concept is the excuse to build something with enough moving parts (jobs, state, background work, data formats) to make the FastAPI learning meaningful rather than a toy CRUD app.

## License

MIT