# DataPump

DataPump is a learning project built to get hands-on with **FastAPI** by building something close to a real-world backend service: a data processing job API.

The core idea is a service that takes in data (starting with CSV, eventually JSON and other formats), "pumps" it through some transformation/processing pipeline, and lands it somewhere useful — a database table, a cleaned dataset, or an input ready for an ML model. The exact shape of the pumping/transformation logic is still being figured out; right now the project focuses on getting the job-management API right first.

> This is a work-in-progress, built for learning purposes. Expect things to change quickly and roughly as the design evolves.

## Current status

What exists today is the **job lifecycle API** — the part of the system responsible for creating, tracking, and updating data-processing jobs. There is no actual CSV/data processing pipeline yet, and no persistent database; jobs are currently stored in an in-memory dict as a stand-in.

Working:
- Create a job with a source, destination, and batch size
- Fetch a job's current status
- Update a job's status/progress (as a background worker would)

Not yet built:
- Actual reading/parsing of CSV or JSON data
- The "pump" step — whatever transformation/processing turns raw input into something useful
- A real database layer (Postgres, SQLite, etc. — currently just an in-memory dict)
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
│   ├── main.py         # FastAPI app + job endpoints
│   ├── models.py        # Pydantic schemas (JobCreate, JobUpdate, JobResponse, JobStatus)
│   └── __init__.py      # Re-exports schemas from models.py
├── app/                 # Reserved for application/business logic (empty for now)
├── database/            # Reserved for the real database layer (empty for now)
├── pyproject.toml
└── README.md
```

> Note: `api/main.py` currently redefines the same schemas found in `api/models.py` instead of importing them. This is a known duplication to clean up as the project settles.

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
| `POST` | `/jobs` | Create a new job |
| `GET` | `/jobs/{job_id}` | Get a job's current status |
| `PATCH` | `/jobs/{job_id}` | Update a job's status/progress (used by a worker) |

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

- [ ] Move shared schemas into `api/models.py` only, drop the duplication in `main.py`
- [ ] Add a real persistence layer under `database/` (likely SQLite/Postgres via SQLAlchemy or SQLModel)
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