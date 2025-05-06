from fastapi import APIRouter, Depends, HTTPException, Body, Request
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone
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
    request: Request,
    current_user: Optional[dict] = None  # Make authentication optional
):
    """
    Record an analysis in history
    """
    try:
        # Get request data
        data = await request.json()

        # Create history record
        history_record = {
            "source_type": data["source_type"],
            "source_name": data["source_name"],
            "record_count": data["record_count"],
            "avg_sentiment_score": data["avg_sentiment_score"],
            "pain_point_count": data["pain_point_count"],
            "feature_request_count": data["feature_request_count"],
            "positive_feedback_count": data["positive_feedback_count"],
            "summary": data["summary"],
            "timestamp": datetime.now(timezone.utc),
            "user_id": current_user.get("id") if current_user else None
        }

        # Insert into database
        result = history_collection.insert_one(history_record)

        # Get the inserted record
        inserted_record = history_collection.find_one({"_id": result.inserted_id})

        # Create response object using the from_mongo method
        response_data = AnalysisHistoryResponse.from_mongo(inserted_record)

        return response_data
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

        history = list(cursor)

        # Create response objects using the from_mongo method
        response_data = []
        for record in history:
            response_data.append(AnalysisHistoryResponse.from_mongo(record))

        return response_data
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
        history = history_collection.find_one({"_id": ObjectId(history_id)})

        if not history:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Create response object using the from_mongo method
        response_data = AnalysisHistoryResponse.from_mongo(history)

        return response_data
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
        history = history_collection.find_one({"_id": ObjectId(history_id)})

        if not history:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Check if user is authorized to delete
        if current_user and history.get("user_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="Not authorized to delete this analysis")

        # Delete the record
        history_collection.delete_one({"_id": ObjectId(history_id)})

        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
