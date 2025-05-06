from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

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

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class AnalysisHistoryCreate(AnalysisHistoryBase):
    pass

class AnalysisHistoryResponse(AnalysisHistoryBase):
    id: str = Field(alias="_id")
    timestamp: datetime
    user_id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """Create a model instance from MongoDB document"""
        if data is None:
            return None

        # Convert ObjectId to string
        if "_id" in data:
            data["_id"] = str(data["_id"])

        return cls(**data)

# Model for analysis history list
class AnalysisHistoryList(BaseModel):
    items: List[AnalysisHistoryResponse]
    total: int
    skip: int = 0
    limit: int = 100
