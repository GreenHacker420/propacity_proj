from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from bson.objectid import ObjectId

from ..models.analysis_history import AnalysisHistoryCreate, AnalysisHistoryResponse, AnalysisHistoryList
from ..services.mongo_history import mongo_history_service
from ..auth.mongo_auth import get_current_active_user
from ..mongodb import get_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/history",
    tags=["history"],
    responses={404: {"description": "Not found"}},
)

# Get MongoDB collection
history_collection = get_collection("analysis_history")

@router.post("", response_model=AnalysisHistoryResponse)  # This will be /history
async def record_analysis(
    analysis_data: AnalysisHistoryCreate,
    current_user: Optional[dict] = None  # Make authentication optional
):
    """
    Record an analysis in history
    """
    try:
        # Create history record
        history_record = {
            "source_type": analysis_data.source_type,
            "source_name": analysis_data.source_name,
            "record_count": analysis_data.record_count,
            "avg_sentiment_score": analysis_data.avg_sentiment_score,
            "pain_point_count": analysis_data.pain_point_count,
            "feature_request_count": analysis_data.feature_request_count,
            "positive_feedback_count": analysis_data.positive_feedback_count,
            "summary": analysis_data.summary,
            "timestamp": datetime.utcnow(),
            "user_id": current_user.get("id") if current_user else None
        }

        # Insert into database
        result = await history_collection.insert_one(history_record)
        
        # Get the inserted record
        inserted_record = await history_collection.find_one({"_id": result.inserted_id})
        
        return {
            "id": str(inserted_record["_id"]),
            "source_type": inserted_record["source_type"],
            "source_name": inserted_record["source_name"],
            "record_count": inserted_record["record_count"],
            "avg_sentiment_score": inserted_record["avg_sentiment_score"],
            "pain_point_count": inserted_record["pain_point_count"],
            "feature_request_count": inserted_record["feature_request_count"],
            "positive_feedback_count": inserted_record["positive_feedback_count"],
            "summary": inserted_record["summary"],
            "timestamp": inserted_record["timestamp"],
            "user_id": inserted_record.get("user_id")
        }
    except Exception as e:
        logger.error(f"Error recording analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[AnalysisHistoryResponse])  # This will be /history
async def get_analysis_history(
    current_user: Optional[dict] = None  # Make authentication optional
):
    """
    Get analysis history
    """
    try:
        # Query history records
        cursor = history_collection.find(
            {"user_id": current_user.get("id") if current_user else None}
        ).sort("timestamp", -1)
        
        history = await cursor.to_list(length=None)
        
        return [
            {
                "id": str(record["_id"]),
                "source_type": record["source_type"],
                "source_name": record["source_name"],
                "record_count": record["record_count"],
                "avg_sentiment_score": record["avg_sentiment_score"],
                "pain_point_count": record["pain_point_count"],
                "feature_request_count": record["feature_request_count"],
                "positive_feedback_count": record["positive_feedback_count"],
                "summary": record["summary"],
                "timestamp": record["timestamp"],
                "user_id": record.get("user_id")
            }
            for record in history
        ]
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{history_id}", response_model=AnalysisHistoryResponse)  # This will be /history/{history_id}
async def get_analysis_by_id(
    history_id: str,
    current_user: Optional[dict] = None  # Make authentication optional
):
    """
    Get a specific analysis history record
    """
    try:
        # Query specific history record
        history = await history_collection.find_one({"_id": ObjectId(history_id)})
        
        if not history:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        return {
            "id": str(history["_id"]),
            "source_type": history["source_type"],
            "source_name": history["source_name"],
            "record_count": history["record_count"],
            "avg_sentiment_score": history["avg_sentiment_score"],
            "pain_point_count": history["pain_point_count"],
            "feature_request_count": history["feature_request_count"],
            "positive_feedback_count": history["positive_feedback_count"],
            "summary": history["summary"],
            "timestamp": history["timestamp"],
            "user_id": history.get("user_id")
        }
    except Exception as e:
        logger.error(f"Error fetching analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{history_id}")  # This will be /history/{history_id}
async def delete_analysis(
    history_id: str,
    current_user: Optional[dict] = None  # Make authentication optional
):
    """
    Delete an analysis history record
    """
    try:
        # Find the history record
        history = await history_collection.find_one({"_id": ObjectId(history_id)})
        
        if not history:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        # Check if user is authorized to delete
        if current_user and history.get("user_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="Not authorized to delete this analysis")
            
        # Delete the record
        await history_collection.delete_one({"_id": ObjectId(history_id)})
        
        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
