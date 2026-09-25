from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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