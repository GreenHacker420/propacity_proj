from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class Review(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None

class ReviewList(BaseModel):
    reviews: List[Review]

class ReviewCreate(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None

class ReviewResponse(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None
    sentiment_score: float
    sentiment_label: str
    category: str
    keywords: List[str]

class ScrapeRequest(BaseModel):
    query: str
    limit: int = 50

class AnalysisResults(BaseModel):
    sentiment_scores: List[float]
    average_rating: float
    review_count: int

class SummaryItem(BaseModel):
    text: str
    sentiment_score: float
    keywords: List[str]

class SummaryResponse(BaseModel):
    pain_points: List[SummaryItem]
    feature_requests: List[SummaryItem]
    positive_feedback: List[SummaryItem]
    suggested_priorities: List[str]

class VisualizationResponse(BaseModel):
    sentiment_chart: Optional[str] = None
    rating_chart: Optional[str] = None
    keyword_chart: Optional[str] = None