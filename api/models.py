import re
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


from pydantic import BaseModel, Field, field_validator, ValidationInfo


class JobStatus(str, Enum):
    """Represents the status of the Job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Model used to create the Job sent by the client."""
    source: str = Field(description="Source of the data.")
    destination: str = Field(description="Destination table of the database.")
    batch_size: int = Field(description="Number of records to process per batch.")
    @field_validator('source', 'destination', mode='after')
    @classmethod
    def validate_non_whitespace(cls, v: str, info: ValidationInfo) -> str:
        field_name = info.field_name.capitalize()
        if not v.strip():
            raise ValueError(f"{field_name} cannot be empty or whitespaces.")
        return v.strip()


id
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
    id: UUID
    source: str
    destination: str
    batch_size: int

    status: JobStatus
    processed_records: int
    total_records: int
    error_message: str

    created_at: datetime
    updated_at: datetime
    completed_at: datetime