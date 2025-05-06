from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
import logging

from ..models.processing_time import ProcessingTimeCreate, ProcessingTimeResponse, EstimatedProcessingTime
from ..services.mongo_timing import mongo_timing_service
from ..auth.mongo_auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/timing",
    tags=["timing"],
    responses={404: {"description": "Not found"}},
)

@router.post("/record", response_model=ProcessingTimeResponse)
async def record_processing_time(
    time_data: ProcessingTimeCreate
):
    """
    Record the time taken for a processing operation
    """
    try:
        result = mongo_timing_service.record_processing_time(time_data.model_dump())
        # Convert ObjectId to string
        result["_id"] = str(result["_id"])
        return result
    except Exception as e:
        logger.error(f"Error recording processing time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estimate/{operation}", response_model=EstimatedProcessingTime)
async def get_estimated_time(
    operation: str,
    record_count: int
):
    """
    Get estimated processing time for an operation
    """
    try:
        result = mongo_timing_service.get_estimated_time(operation, record_count)
        return result
    except Exception as e:
        logger.error(f"Error getting estimated time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ProcessingTimeResponse])
async def get_processing_time_history(
    operation: Optional[str] = None,
    limit: int = 100,
    current_user: Optional[dict] = Depends(get_current_active_user)
):
    """
    Get processing time history
    """
    try:
        results = mongo_timing_service.get_all_processing_times(operation, limit)
        # Convert ObjectId to string in each result
        for result in results:
            if "_id" in result and not isinstance(result["_id"], str):
                result["_id"] = str(result["_id"])
        return results
    except Exception as e:
        logger.error(f"Error getting processing time history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
