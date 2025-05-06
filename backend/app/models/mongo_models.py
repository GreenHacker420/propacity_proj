"""
MongoDB models for the Product Review Analyzer.
This module provides functions to convert between SQLAlchemy models and MongoDB documents.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator

# Helper function to convert string to ObjectId
def convert_object_id(id: Any) -> ObjectId:
    if isinstance(id, ObjectId):
        return id
    if isinstance(id, str):
        return ObjectId(id)
    raise ValueError(f"Cannot convert {id} to ObjectId")

# Type for MongoDB ObjectId fields
PyObjectId = Annotated[ObjectId, BeforeValidator(convert_object_id)]

# Base MongoDB model with ID field
class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

# MongoDB User model
class MongoUser(MongoBaseModel):
    email: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sqlalchemy(cls, user):
        """Convert SQLAlchemy User model to MongoDB User model"""
        return cls(
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            is_admin=user.is_admin
        )

# MongoDB Keyword model
class MongoKeyword(MongoBaseModel):
    text: str

    @classmethod
    def from_sqlalchemy(cls, keyword):
        """Convert SQLAlchemy Keyword model to MongoDB Keyword model"""
        return cls(
            text=keyword.text
        )

# MongoDB Review model
class MongoReview(MongoBaseModel):
    text: str
    username: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    rating: Optional[float] = None
    sentiment_score: float
    sentiment_label: str
    category: str
    source: Optional[str] = None
    user_id: Optional[str] = None
    keywords: List[str] = []

    @classmethod
    def from_sqlalchemy(cls, review):
        """Convert SQLAlchemy Review model to MongoDB Review model"""
        return cls(
            text=review.text,
            username=review.username,
            timestamp=review.timestamp,
            rating=review.rating,
            sentiment_score=review.sentiment_score,
            sentiment_label=review.sentiment_label,
            category=review.category,
            source=review.source,
            user_id=str(review.user_id) if review.user_id else None,
            keywords=[keyword.text for keyword in review.keywords]
        )

# MongoDB AnalysisHistory model
class MongoAnalysisHistory(MongoBaseModel):
    source_type: str
    source_name: str
    record_count: int
    avg_sentiment_score: float
    pain_point_count: int
    feature_request_count: int
    positive_feedback_count: int
    summary: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None

    @classmethod
    def from_sqlalchemy(cls, history):
        """Convert SQLAlchemy AnalysisHistory model to MongoDB AnalysisHistory model"""
        return cls(
            source_type=history.source_type,
            source_name=history.source_name,
            record_count=history.record_count,
            avg_sentiment_score=history.avg_sentiment_score,
            pain_point_count=history.pain_point_count,
            feature_request_count=history.feature_request_count,
            positive_feedback_count=history.positive_feedback_count,
            summary=history.summary,
            timestamp=history.timestamp,
            user_id=str(history.user_id) if history.user_id else None
        )

# MongoDB ProcessingTime model
class MongoProcessingTime(MongoBaseModel):
    operation: str
    file_name: Optional[str] = None
    source: Optional[str] = None
    query: Optional[str] = None
    record_count: int
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_sqlalchemy(cls, processing_time):
        """Convert SQLAlchemy ProcessingTime model to MongoDB ProcessingTime model"""
        return cls(
            operation=processing_time.operation,
            file_name=processing_time.file_name,
            source=processing_time.source,
            query=processing_time.query,
            record_count=processing_time.record_count,
            duration_seconds=processing_time.duration_seconds,
            timestamp=processing_time.timestamp
        )
