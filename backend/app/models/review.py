from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewCreate(ReviewBase):
    pass

class ReviewAnalysis(ReviewBase):
    sentiment_score: float
    sentiment_label: str
    category: str  # pain_point, feature_request, or positive_feedback
    keywords: list[str]

class ReviewResponse(ReviewAnalysis):
    id: int

    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    source: str = Field(..., pattern="^(twitter|playstore)$")
    query: Optional[str] = None
    app_id: Optional[str] = None
    limit: Optional[int] = Field(50, ge=1, le=1000)

class SummaryResponse(BaseModel):
    pain_points: list[dict]
    feature_requests: list[dict]
    positive_feedback: list[dict]
    suggested_priorities: list[str] 