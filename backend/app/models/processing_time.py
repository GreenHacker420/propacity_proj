from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Pydantic models for API
class ProcessingTimeBase(BaseModel):
    operation: str
    file_name: Optional[str] = None
    source: Optional[str] = None
    query: Optional[str] = None
    record_count: int
    duration_seconds: float

class ProcessingTimeCreate(ProcessingTimeBase):
    pass

class ProcessingTimeResponse(ProcessingTimeBase):
    id: str = Field(alias="_id")
    timestamp: datetime

    class Config:
        populate_by_name = True
        from_attributes = True

# Model for estimated processing times
class EstimatedProcessingTime(BaseModel):
    operation: str
    record_count: int
    estimated_seconds: float
    confidence: str
    based_on_samples: int
