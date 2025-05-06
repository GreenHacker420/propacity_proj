from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional
from ..database import Base

# Association table for keywords
review_keyword = Table(
    'review_keyword',
    Base.metadata,
    Column('review_id', Integer, ForeignKey('reviews.id')),
    Column('keyword_id', Integer, ForeignKey('keywords.id'))
)

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True)
    
    # Relationships
    reviews = relationship("Review", secondary=review_keyword, back_populates="keywords")
    
    def __repr__(self):
        return f"<Keyword {self.text}>"

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    username = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    rating = Column(Float, nullable=True)
    sentiment_score = Column(Float)
    sentiment_label = Column(String)
    category = Column(String)
    source = Column(String, nullable=True)  # e.g., "twitter", "playstore", "csv"
    
    # User relationship (if authenticated)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="reviews")
    
    # Keywords relationship
    keywords = relationship("Keyword", secondary=review_keyword, back_populates="reviews")
    
    def __repr__(self):
        return f"<Review {self.id}: {self.text[:30]}...>"
    
    @property
    def keywords_list(self) -> List[str]:
        """Return a list of keyword strings"""
        return [keyword.text for keyword in self.keywords]
