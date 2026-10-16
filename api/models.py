"""Data models for job management in DataPump.

This module defines Pydantic models and enums used for creating, updating,
and serializing data pipeline jobs within the DataPump application.
"""

import re
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class JobStatus(str, Enum):
    """Represents the execution status of a data pipeline job.

    Attributes:
        PENDING: Job has been created but not yet started.
        PROCESSING: Job is currently being executed by a worker.
        COMPLETED: Job finished successfully.
        FAILED: Job encountered an error and failed execution.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Payload model used by clients to create a new data pipeline job.

    Attributes:
        job_source: Source identifier or connection string for the data.
        destination: Target table or destination endpoint in the database.
        batch_size: Number of records to process per batch (default 1000, max 10000).
    """

    job_source: str = Field(description="Source of the data.")
    destination: str = Field(description="Destination table of the database.")
    batch_size: int = Field(
        default=1000,
        gt=0,
        le=10000,
        description="Number of records to process per batch.",
    )

    @field_validator("job_source", "destination", mode="after")
    @classmethod
    def validate_non_whitespace(cls, v: str, info: ValidationInfo) -> str:
        """Validates that string fields are not empty or solely whitespace.

        Args:
            v: The string value to validate.
            info: Validation context containing field metadata.

        Returns:
            The stripped, validated string value.

        Raises:
            ValueError: If the string is empty or contains only whitespace.
        """
        field_name = info.field_name.capitalize()
        if not v.strip():
            raise ValueError(f"{field_name} cannot be empty or whitespaces.")
        return v.strip()


class JobUpdate(BaseModel):
    """Internal model used by workers to update job progress and status.

    Attributes:
        status: Current execution status of the job.
        processed_records: Total number of records processed so far.
        total_records: Total number of records targeted for processing.
        error_message: Detailed error message if the job failed.
    """

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
    """Response model returned to clients when querying job details and status.

    Attributes:
        id: Unique identifier (UUID) for the job.
        job_source: Source identifier or connection string for the data.
        destination: Target table or destination endpoint in the database.
        batch_size: Number of records processed per batch.
        status: Current execution status of the job.
        processed_records: Total number of records processed so far.
        total_records: Total number of records targeted for processing.
        error_message: Error message if the job failed, otherwise None.
        created_at: Timestamp when the job was created.
        updated_at: Timestamp when the job was last updated.
        completed_at: Timestamp when the job finished execution.
    """

    id: UUID
    job_source: str
    destination: str
    batch_size: int

    status: JobStatus
    processed_records: int
    total_records: int
    error_message: str | None

    created_at: datetime
    updated_at: datetime | None
    completed_at: datetime | None