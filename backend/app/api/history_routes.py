from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
import logging

from ..models.analysis_history import AnalysisHistoryCreate, AnalysisHistoryResponse, AnalysisHistoryList
from ..services.mongo_history import mongo_history_service
from ..auth.mongo_auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/history",
    tags=["history"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=AnalysisHistoryResponse)
async def record_analysis(
    history_data: AnalysisHistoryCreate,
    current_user: Optional[dict] = Depends(get_current_active_user)
):
    """
    Record an analysis in the history
    """
    try:
        user_id = str(current_user["_id"]) if current_user else None
        return mongo_history_service.record_analysis(history_data.dict(), user_id)
    except Exception as e:
        logger.error(f"Error recording analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=AnalysisHistoryList)
async def get_analysis_history(
    source_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[dict] = Depends(get_current_active_user)
):
    """
    Get analysis history
    """
    try:
        user_id = str(current_user["_id"]) if current_user else None
        return mongo_history_service.get_analysis_history(user_id, source_type, skip, limit)
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}", response_model=AnalysisHistoryResponse)
async def get_analysis_by_id(
    analysis_id: str
):
    """
    Get a specific analysis history record by ID
    """
    try:
        db_history = mongo_history_service.get_analysis_by_id(analysis_id)
        if db_history is None:
            raise HTTPException(status_code=404, detail="Analysis history not found")
        return db_history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{analysis_id}", response_model=bool)
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete an analysis history record (requires authentication)
    """
    try:
        # Check if the analysis belongs to the user
        db_history = mongo_history_service.get_analysis_by_id(analysis_id)
        if db_history is None:
            raise HTTPException(status_code=404, detail="Analysis history not found")

        # Check if the user is authorized to delete this analysis
        if db_history.get("user_id") != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized to delete this analysis")

        return mongo_history_service.delete_analysis(analysis_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
