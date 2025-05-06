from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from ..models.processing_time import ProcessingTimeCreate, ProcessingTimeResponse, EstimatedProcessingTime
from ..services.timing import timing_service
from ..database import get_db
from ..auth.security import get_current_active_user
from ..models.user import User

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
    time_data: ProcessingTimeCreate,
    db: Session = Depends(get_db)
):
    """
    Record the time taken for a processing operation
    """
    try:
        return timing_service.record_processing_time(db, time_data)
    except Exception as e:
        logger.error(f"Error recording processing time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/estimate/{operation}", response_model=EstimatedProcessingTime)
async def get_estimated_time(
    operation: str,
    record_count: int,
    db: Session = Depends(get_db)
):
    """
    Get estimated processing time for an operation
    """
    try:
        return timing_service.get_estimated_time(db, operation, record_count)
    except Exception as e:
        logger.error(f"Error getting estimated time: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ProcessingTimeResponse])
async def get_processing_time_history(
    operation: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get processing time history (requires authentication)
    """
    try:
        return timing_service.get_all_processing_times(db, operation, limit)
    except Exception as e:
        logger.error(f"Error getting processing time history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
