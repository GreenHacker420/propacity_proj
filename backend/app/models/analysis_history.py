from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..database import Base

# SQLAlchemy model for storing analysis history
class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String, index=True)  # "csv", "twitter", "playstore", "github"
    source_name = Column(String)  # File name, query, or app ID
    record_count = Column(Integer)  # Number of records analyzed
    avg_sentiment_score = Column(Float)  # Average sentiment score
    pain_point_count = Column(Integer)  # Number of pain points
    feature_request_count = Column(Integer)  # Number of feature requests
    positive_feedback_count = Column(Integer)  # Number of positive feedback items
    summary = Column(JSON)  # JSON summary data
    timestamp = Column(DateTime, default=datetime.now)
    
    # User relationship (if authenticated)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="analysis_history")
    
    def __repr__(self):
        return f"<AnalysisHistory {self.id}: {self.source_type} - {self.source_name}>"

# Add relationship to User model
from ..models.user import User
User.analysis_history = relationship("AnalysisHistory", back_populates="user")

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
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# Model for analysis history list
class AnalysisHistoryList(BaseModel):
    items: List[AnalysisHistoryResponse]
    total: int
