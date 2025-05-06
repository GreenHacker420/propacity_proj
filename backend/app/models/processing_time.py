from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy model for storing processing times
class ProcessingTime(Base):
    __tablename__ = "processing_times"
    
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String, index=True)  # e.g., "upload", "scrape", "sentiment_analysis"
    file_name = Column(String, nullable=True)  # For upload operations
    source = Column(String, nullable=True)  # For scrape operations
    query = Column(String, nullable=True)  # For scrape operations
    record_count = Column(Integer)  # Number of records processed
    duration_seconds = Column(Float)  # Time taken in seconds
    timestamp = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<ProcessingTime {self.operation}: {self.duration_seconds}s for {self.record_count} records>"

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
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Model for estimated processing times
class EstimatedProcessingTime(BaseModel):
    operation: str
    estimated_seconds: float
    estimated_seconds_per_record: float
