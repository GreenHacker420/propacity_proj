from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from bson.objectid import ObjectId

from ..models.weekly_summary import WeeklySummaryCreate, WeeklySummaryResponse
from ..services.weekly_summary import WeeklySummaryService
from ..auth.mongo_auth import get_current_active_user
from ..mongodb import get_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/weekly",
    tags=["weekly"],
    responses={404: {"description": "Not found"}},
)

# Initialize service
weekly_service = WeeklySummaryService()

@router.post("/summary", response_model=WeeklySummaryResponse)
async def create_weekly_summary(
    source_type: str,
    source_name: str,
    current_user: Optional[dict] = None
):
    """
    Generate a weekly summary of feedback for a specific source
    """
    try:
        # Get the date range for the past week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Generate summary
        summary = await weekly_service.generate_summary(
            source_type=source_type,
            source_name=source_name,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.get("id") if current_user else None
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error generating weekly summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{summary_id}", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    summary_id: str,
    current_user: Optional[dict] = None
):
    """
    Get a specific weekly summary by ID
    """
    try:
        summary = await weekly_service.get_summary_by_id(summary_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Weekly summary not found")
        return summary
    except Exception as e:
        logger.error(f"Error fetching weekly summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summaries", response_model=List[WeeklySummaryResponse])
async def get_weekly_summaries(
    source_type: Optional[str] = None,
    current_user: Optional[dict] = None
):
    """
    Get all weekly summaries, optionally filtered by source type
    """
    try:
        summaries = await weekly_service.get_summaries(
            source_type=source_type,
            user_id=current_user.get("id") if current_user else None
        )
        return summaries
    except Exception as e:
        logger.error(f"Error fetching weekly summaries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/priorities", response_model=Dict[str, Any])
async def get_priority_insights(
    source_type: Optional[str] = None,
    current_user: Optional[dict] = None
):
    """
    Get prioritized insights from recent feedback
    """
    try:
        insights = await weekly_service.get_priority_insights(
            source_type=source_type,
            user_id=current_user.get("id") if current_user else None
        )
        return insights
    except Exception as e:
        logger.error(f"Error getting priority insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 