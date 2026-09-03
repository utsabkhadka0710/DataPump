from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Represents the status of the Job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    """Model used to creat the Job sent by the client."""
    source: str = Field(..., description="Source of the data.")
    destination: str = Field(...,min_length=1 ,description="Destination table of the database.")
    batch_size: int = Field(
        default=1000,
        gt=0,
        le=10000,
        description="Numbers of records to process per batch."
    )
    
class JobUpdate(BaseModel):
    """Model used internally by the worker to update the progress of Job in background."""
    status: Optional[JobStatus] = Field(
        default=None, description="Status of the job."
    )
    processed_records: Optional[int] = Field(
        default=None, description="Total no.of processed records."
    )
    total_records: Optional[int] = Field(
        default=None, description="Total no.of records given inorder to process."
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message is there was a failure in processing the Job."
    )
    
class JobResponse(BaseModel):
    """Model returned to the client when job status is requested."""
    id: UUID = Field(
        default_factory=uuid4, description="Unique Job id."
    )
    source: str
    destination: str
    batch_size: int
    
    status: JobStatus = JobStatus.PENDING
    processed_records:int = 0
    total_records:int = 0
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime|None = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    