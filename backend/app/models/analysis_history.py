from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Pydantic models for API
class AnalysisHistoryBase(BaseModel):
    source_type: str
    source_name: str
    record_count: int
    avg_sentiment_score: float
    pain_point_count: int
    feature_request_count: int
    positive_feedback_count: int
    summary: Dict[str, Any]

class AnalysisHistoryCreate(AnalysisHistoryBase):
    pass

class AnalysisHistoryResponse(AnalysisHistoryBase):
    id: str = Field(alias="_id")
    timestamp: datetime
    user_id: Optional[str] = None

    class Config:
        populate_by_name = True
        from_attributes = True

# Model for analysis history list
class AnalysisHistoryList(BaseModel):
    items: List[AnalysisHistoryResponse]
    total: int
    skip: int = 0
    limit: int = 100
