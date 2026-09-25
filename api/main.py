from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# 1. Enums & Schemas
# -------------------------------------------------------------------

class JobStatus(str, Enum):
    """Represents the status of the Job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Model used to create the Job sent by the client."""
    source: str = Field(description="Source of the data.")
    destination: str = Field(
        min_length=1, description="Destination table of the database."
    )
    batch_size: int = Field(
        default=1000,
        gt=0,
        le=10000,
        description="Number of records to process per batch."
    )


class JobUpdate(BaseModel):
    """Model used internally by the worker to update the progress of Job in background."""
    status: JobStatus | None = Field(
        default=None, description="Status of the job."
    )
    processed_records: int | None = Field(
        default=None, description="Total number of processed records."
    )
    total_records: int | None = Field(
        default=None, description="Total number of records given in order to process."
    )
    error_message: str | None = Field(
        default=None, description="Error message if there was a failure in processing the Job."
    )


class JobResponse(BaseModel):
    """Model returned to the client when job status is requested."""
    id: UUID = Field(
        default_factory=uuid4, description="Unique Job ID."
    )
    source: str
    destination: str
    batch_size: int

    status: JobStatus = JobStatus.PENDING
    processed_records: int = 0
    total_records: int = 0
    error_message: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    completed_at: datetime | None = None


# -------------------------------------------------------------------
# 2. In-Memory Mock Database (Temporal Layer)
# -------------------------------------------------------------------

# Key: UUID, Value: JobResponse instance
fake_db: dict[UUID, JobResponse] = {}


# -------------------------------------------------------------------
# 3. API Routes
# -------------------------------------------------------------------

app = FastAPI(title="Job Processing API (Mock In-Memory Layer)")


@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate) -> JobResponse:
    """Client creates a new job."""
    new_job = JobResponse(
        source=payload.source,
        destination=payload.destination,
        batch_size=payload.batch_size,
    )
    fake_db[new_job.id] = new_job
    return new_job


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    """Fetch job status by ID."""
    if job_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )
    return fake_db[job_id]


@app.patch("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, payload: JobUpdate) -> JobResponse:
    """Background worker updates job status and progress."""
    if job_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    current_job = fake_db[job_id]

    # Extract provided non-None fields
    update_data = payload.model_dump(exclude_unset=True)

    # Automatically handle updated_at and completed_at timestamps
    now = datetime.now(timezone.utc)
    update_data["updated_at"] = now

    if payload.status in (JobStatus.COMPLETED, JobStatus.FAILED):
        update_data["completed_at"] = now

    # Create updated instance and replace in fake_db
    updated_job = current_job.model_copy(update=update_data)
    fake_db[job_id] = updated_job

    return updated_job