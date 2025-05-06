from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PriorityItem(BaseModel):
    """A prioritized item from user feedback"""
    title: str
    description: str
    priority_score: float
    category: str  # pain_point, feature_request, positive_feedback
    sentiment_score: float
    frequency: int
    examples: List[str]

class WeeklySummaryBase(BaseModel):
    """Base model for weekly summary data"""
    source_type: str
    source_name: str
    start_date: datetime
    end_date: datetime
    total_reviews: int
    avg_sentiment_score: float
    pain_points: List[PriorityItem]
    feature_requests: List[PriorityItem]
    positive_feedback: List[PriorityItem]
    top_keywords: Dict[str, int]
    trend_analysis: Dict[str, Any]
    recommendations: List[str]

class WeeklySummaryCreate(WeeklySummaryBase):
    """Model for creating a new weekly summary"""
    pass

class WeeklySummaryResponse(WeeklySummaryBase):
    """Model for weekly summary response"""
    id: str = Field(alias="_id")
    created_at: datetime
    user_id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class PriorityInsights(BaseModel):
    """Model for priority insights"""
    high_priority_items: List[PriorityItem]
    trending_topics: List[Dict[str, Any]]
    sentiment_trends: Dict[str, float]
    action_items: List[str]
    risk_areas: List[str]
    opportunity_areas: List[str]