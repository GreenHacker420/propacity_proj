"""
MongoDB-compatible models for the Product Review Analyzer.
These are not SQLAlchemy models but simple dictionaries that represent MongoDB documents.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# MongoDB document structure for keywords
class KeywordModel(BaseModel):
    """Pydantic model for keywords"""
    id: Optional[str] = Field(None, alias="_id")
    text: str

    class Config:
        populate_by_name = True

# MongoDB document structure for reviews
class ReviewModel(BaseModel):
    """Pydantic model for reviews"""
    id: Optional[str] = Field(None, alias="_id")
    text: str
    username: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    rating: Optional[float] = None
    sentiment_score: float
    sentiment_label: str
    category: str = "general"
    source: Optional[str] = None  # e.g., "twitter", "playstore", "csv"
    user_id: Optional[str] = None
    keywords: List[str] = []

    class Config:
        populate_by_name = True

    @property
    def keywords_list(self) -> List[str]:
        """Return a list of keyword strings"""
        return self.keywords

# For backward compatibility
class Review:
    """
    Compatibility class for code that expects SQLAlchemy models.
    This is a wrapper around a MongoDB document.
    """
    def __init__(self, document: Dict[str, Any]):
        self._document = document
        self.id = str(document.get("_id", ""))
        self.text = document.get("text", "")
        self.username = document.get("username")
        self.timestamp = document.get("timestamp", datetime.now())
        self.rating = document.get("rating")
        self.sentiment_score = document.get("sentiment_score", 0.0)
        self.sentiment_label = document.get("sentiment_label", "NEUTRAL")
        self.category = document.get("category", "general")
        self.source = document.get("source")
        self.user_id = document.get("user_id")
        self.keywords = document.get("keywords", [])

    def __repr__(self):
        return f"<Review {self.id}: {self.text[:30]}...>"

    @property
    def keywords_list(self) -> List[str]:
        """Return a list of keyword strings"""
        return self.keywords

# For backward compatibility
class Keyword:
    """
    Compatibility class for code that expects SQLAlchemy models.
    This is a wrapper around a MongoDB document.
    """
    def __init__(self, document: Dict[str, Any]):
        self._document = document
        self.id = str(document.get("_id", ""))
        self.text = document.get("text", "")

    def __repr__(self):
        return f"<Keyword {self.text}>"
