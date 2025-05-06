"""
MongoDB service for storing and retrieving data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..mongodb import get_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoService:
    """
    Service for interacting with MongoDB.
    """
    
    @staticmethod
    def store_review(
        text: str,
        sentiment_score: float,
        sentiment_label: str,
        username: Optional[str] = None,
        rating: Optional[float] = None,
        category: str = "general",
        source: Optional[str] = None,
        user_id: Optional[str] = None,
        keywords: List[str] = []
    ) -> str:
        """
        Store a review in MongoDB.
        
        Args:
            text: The review text
            sentiment_score: The sentiment score (0-1)
            sentiment_label: The sentiment label (POSITIVE, NEGATIVE, NEUTRAL)
            username: Optional username of the reviewer
            rating: Optional rating (0-5)
            category: Category of the review
            source: Source of the review
            user_id: Optional user ID
            keywords: List of keywords
            
        Returns:
            ID of the stored review
        """
        try:
            reviews_collection = get_collection("reviews")
            
            # Create review document
            review = {
                "text": text,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "timestamp": datetime.now(),
                "category": category
            }
            
            # Add optional fields
            if username:
                review["username"] = username
            if rating is not None:
                review["rating"] = rating
            if source:
                review["source"] = source
            if user_id:
                review["user_id"] = user_id
            if keywords:
                review["keywords"] = keywords
                
            # Insert review
            result = reviews_collection.insert_one(review)
            logger.info(f"Stored review in MongoDB with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing review in MongoDB: {str(e)}")
            return None
    
    @staticmethod
    def store_analysis_history(
        source_type: str,
        source_name: str,
        record_count: int,
        avg_sentiment_score: float,
        pain_point_count: int,
        feature_request_count: int,
        positive_feedback_count: int,
        summary: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """
        Store analysis history in MongoDB.
        
        Args:
            source_type: Type of source (e.g., "csv", "twitter", "playstore")
            source_name: Name of the source
            record_count: Number of records analyzed
            avg_sentiment_score: Average sentiment score
            pain_point_count: Number of pain points identified
            feature_request_count: Number of feature requests identified
            positive_feedback_count: Number of positive feedback items
            summary: Summary of the analysis
            user_id: Optional user ID
            
        Returns:
            ID of the stored analysis history
        """
        try:
            history_collection = get_collection("analysis_history")
            
            # Create history document
            history = {
                "source_type": source_type,
                "source_name": source_name,
                "record_count": record_count,
                "avg_sentiment_score": avg_sentiment_score,
                "pain_point_count": pain_point_count,
                "feature_request_count": feature_request_count,
                "positive_feedback_count": positive_feedback_count,
                "summary": summary,
                "timestamp": datetime.now()
            }
            
            # Add optional fields
            if user_id:
                history["user_id"] = user_id
                
            # Insert history
            result = history_collection.insert_one(history)
            logger.info(f"Stored analysis history in MongoDB with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing analysis history in MongoDB: {str(e)}")
            return None
    
    @staticmethod
    def store_processing_time(
        operation: str,
        record_count: int,
        duration_seconds: float,
        file_name: Optional[str] = None,
        source: Optional[str] = None,
        query: Optional[str] = None
    ) -> str:
        """
        Store processing time in MongoDB.
        
        Args:
            operation: Name of the operation
            record_count: Number of records processed
            duration_seconds: Duration in seconds
            file_name: Optional file name
            source: Optional source
            query: Optional query
            
        Returns:
            ID of the stored processing time
        """
        try:
            times_collection = get_collection("processing_times")
            
            # Create processing time document
            processing_time = {
                "operation": operation,
                "record_count": record_count,
                "duration_seconds": duration_seconds,
                "timestamp": datetime.now()
            }
            
            # Add optional fields
            if file_name:
                processing_time["file_name"] = file_name
            if source:
                processing_time["source"] = source
            if query:
                processing_time["query"] = query
                
            # Insert processing time
            result = times_collection.insert_one(processing_time)
            logger.info(f"Stored processing time in MongoDB with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing processing time in MongoDB: {str(e)}")
            return None
