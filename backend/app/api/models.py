from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class Review(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None
    source: Optional[str] = None

class ReviewList(BaseModel):
    reviews: List[Review]

class ReviewCreate(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None
    source: Optional[str] = None

class ReviewResponse(BaseModel):
    text: str
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    rating: Optional[float] = None
    sentiment_score: float
    sentiment_label: str
    category: str
    keywords: List[str]
    source: Optional[str] = None
    detected_language: Optional[str] = None
    is_translated: Optional[bool] = None
    original_text: Optional[str] = None

class ScrapeRequest(BaseModel):
    source: str = Field(..., description="Source to scrape (twitter, playstore)")
    query: Optional[str] = Field(None, description="Search query for Twitter")
    app_id: Optional[str] = Field(None, description="App ID for Play Store")
    limit: int = Field(50, description="Maximum number of results to return")

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

# Advanced analysis models
class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int

class EntityAnalysisResponse(BaseModel):
    entities: List[Entity]
    entity_counts: Dict[str, Dict[str, int]]
    product_mentions: Dict[str, int]

class Topic(BaseModel):
    id: int
    words: List[str]
    weight: float

class TopicModelingResponse(BaseModel):
    topics: List[Topic]
    topic_distribution: Optional[str] = None

class AspectSentiment(BaseModel):
    aspect: str
    context: str
    sentiment_score: float
    sentiment_label: str

class AspectAnalysisResponse(BaseModel):
    aspects: Dict[str, Dict[str, Any]]
    visualization: Optional[str] = None

class EmotionAnalysisResponse(BaseModel):
    emotions: Dict[str, int]
    percentages: Dict[str, float]
    visualization: Optional[str] = None

class TimeMetrics(BaseModel):
    time_period: datetime
    review_count: int
    avg_sentiment: Optional[float] = None
    avg_rating: Optional[float] = None
    positive_count: int
    neutral_count: int
    negative_count: int

class TrendAnalysisResponse(BaseModel):
    time_metrics: List[TimeMetrics]
    sentiment_trend: Optional[str] = None
    rating_trend: Optional[str] = None
    volume_trend: Optional[str] = None

class Cluster(BaseModel):
    id: int
    size: int
    top_terms: List[str]
    avg_sentiment: float
    dominant_sentiment: str
    sample_reviews: List[str]

class ClusteringResponse(BaseModel):
    clusters: List[Cluster]
    visualization: Optional[str] = None

class InsightsResponse(BaseModel):
    key_insights: List[str]
    improvement_areas: List[str]
    strengths: List[str]
    opportunities: List[str]

class LanguageAnalysisResponse(BaseModel):
    language_distribution: Dict[str, int]
    language_names: Dict[str, str]

class AdvancedAnalysisRequest(BaseModel):
    reviews: List[ReviewResponse]
    analysis_types: List[str] = Field(
        ["all"],
        description="Types of analysis to perform: entities, topics, aspects, emotions, trends, clusters, insights, languages"
    )
    time_period: str = Field("month", description="Time period for trend analysis: day, week, month")
    n_topics: int = Field(5, description="Number of topics for topic modeling")
    n_clusters: int = Field(5, description="Number of clusters for clustering")
    target_language: str = Field("en", description="Target language for translation")

class AdvancedAnalysisResponse(BaseModel):
    entity_analysis: Optional[EntityAnalysisResponse] = None
    topic_modeling: Optional[TopicModelingResponse] = None
    aspect_analysis: Optional[AspectAnalysisResponse] = None
    emotion_analysis: Optional[EmotionAnalysisResponse] = None
    trend_analysis: Optional[TrendAnalysisResponse] = None
    clustering: Optional[ClusteringResponse] = None
    insights: Optional[InsightsResponse] = None
    language_analysis: Optional[LanguageAnalysisResponse] = None