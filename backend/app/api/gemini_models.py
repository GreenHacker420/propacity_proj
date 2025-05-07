"""
Models for Gemini API integration.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GeminiSentimentRequest(BaseModel):
    """Request model for Gemini sentiment analysis."""
    text: str = Field(..., description="Text to analyze")

class GeminiSentimentResponse(BaseModel):
    """Response model for Gemini sentiment analysis."""
    score: float = Field(..., description="Sentiment score between 0 (negative) and 1 (positive)")
    label: str = Field(..., description="Sentiment label: POSITIVE, NEGATIVE, or NEUTRAL")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class GeminiBatchRequest(BaseModel):
    """Request model for batch processing with Gemini."""
    texts: List[str] = Field(..., description="List of texts to analyze")

class GeminiBatchResponse(BaseModel):
    """Response model for batch processing with Gemini."""
    results: List[GeminiSentimentResponse] = Field(..., description="List of sentiment analysis results")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")

class GeminiInsightRequest(BaseModel):
    """Request model for extracting insights with Gemini."""
    reviews: List[str] = Field(..., description="List of review texts to analyze")

class GeminiInsightResponse(BaseModel):
    """Response model for insights extracted with Gemini."""
    summary: str = Field(..., description="Summary of the reviews")
    key_points: List[str] = Field(..., description="Key points extracted from reviews")
    pain_points: List[str] = Field(..., description="Pain points mentioned in reviews")
    feature_requests: List[str] = Field(..., description="Feature requests mentioned in reviews")
    positive_aspects: List[str] = Field(..., description="Positive aspects mentioned in reviews")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")

class GeminiStatusResponse(BaseModel):
    """Response model for Gemini service status."""
    available: bool = Field(..., description="Whether the Gemini API is available")
    model: str = Field(..., description="The Gemini model being used")
    rate_limited: bool = Field(..., description="Whether the service is currently rate limited")
    circuit_open: bool = Field(..., description="Whether the circuit breaker is open")
    using_local_processing: bool = Field(..., description="Whether local processing is being used")
    rate_limit_reset_in: Optional[int] = Field(None, description="Seconds until rate limit resets")
    circuit_reset_in: Optional[int] = Field(None, description="Seconds until circuit breaker resets")
