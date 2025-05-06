"""
MongoDB-based history service for the Product Review Analyzer.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pydantic import BaseModel

from ..mongodb import get_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoHistoryService:
    """Service for managing analysis history in MongoDB."""
    
    @staticmethod
    def record_analysis(
        history_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an analysis in the history.
        
        Args:
            history_data: Analysis history data
            user_id: Optional user ID
            
        Returns:
            Recorded analysis history
        """
        try:
            history_collection = get_collection("analysis_history")
            
            # Create history document
            history = {
                "source_type": history_data.get("source_type"),
                "source_name": history_data.get("source_name"),
                "record_count": history_data.get("record_count", 0),
                "avg_sentiment_score": history_data.get("avg_sentiment_score", 0.0),
                "pain_point_count": history_data.get("pain_point_count", 0),
                "feature_request_count": history_data.get("feature_request_count", 0),
                "positive_feedback_count": history_data.get("positive_feedback_count", 0),
                "summary": history_data.get("summary", {}),
                "timestamp": datetime.now()
            }
            
            # Add user ID if provided
            if user_id:
                history["user_id"] = user_id
                
            # Insert history
            result = history_collection.insert_one(history)
            history["_id"] = result.inserted_id
            
            logger.info(f"Recorded analysis history with ID: {result.inserted_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error recording analysis history: {str(e)}")
            raise
    
    @staticmethod
    def get_analysis_history(
        user_id: Optional[str] = None,
        source_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get analysis history.
        
        Args:
            user_id: Optional user ID to filter by
            source_type: Optional source type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of analysis history records
        """
        try:
            history_collection = get_collection("analysis_history")
            
            # Build query
            query = {}
            if user_id:
                query["user_id"] = user_id
            if source_type:
                query["source_type"] = source_type
                
            # Get total count
            total_count = history_collection.count_documents(query)
            
            # Get history records
            history_records = list(
                history_collection.find(query)
                .sort("timestamp", -1)
                .skip(skip)
                .limit(limit)
            )
            
            # Convert ObjectId to string
            for record in history_records:
                record["_id"] = str(record["_id"])
                
            return {
                "items": history_records,
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            raise
    
    @staticmethod
    def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific analysis history record by ID.
        
        Args:
            analysis_id: Analysis history ID
            
        Returns:
            Analysis history record or None if not found
        """
        try:
            history_collection = get_collection("analysis_history")
            
            # Get history record
            history = history_collection.find_one({"_id": ObjectId(analysis_id)})
            
            if history:
                history["_id"] = str(history["_id"])
                
            return history
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            raise
    
    @staticmethod
    def delete_analysis(analysis_id: str) -> bool:
        """
        Delete an analysis history record.
        
        Args:
            analysis_id: Analysis history ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            history_collection = get_collection("analysis_history")
            
            # Delete history record
            result = history_collection.delete_one({"_id": ObjectId(analysis_id)})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting analysis history: {str(e)}")
            raise

# Create singleton instance
mongo_history_service = MongoHistoryService()
