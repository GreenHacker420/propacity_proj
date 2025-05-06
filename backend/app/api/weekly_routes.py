from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from ..models.weekly_summary import WeeklySummaryCreate, WeeklySummaryResponse, PriorityInsights
from ..services.weekly_summary_service import WeeklySummaryService
from ..auth.mongo_auth import get_current_active_user
from ..mongodb import get_collection, get_connection_status

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
        end_date = datetime.now(datetime.timezone.utc)
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
        return insights.model_dump() if hasattr(insights, 'model_dump') else (insights.dict() if hasattr(insights, 'dict') else insights)
    except Exception as e:
        logger.error(f"Error getting priority insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_weekly_summary():
    """
    Comprehensive test endpoint to verify MongoDB connection and weekly summary functionality.
    Creates a test summary and verifies all operations.
    """
    try:
        # 1. Test MongoDB connection
        status = await get_connection_status()
        if status["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"MongoDB connection error: {status['error']}"
            )

        # 2. Create a test summary
        test_summary = WeeklySummaryCreate(
            source_type="test",
            source_name="test_app",
            start_date=datetime.now(datetime.timezone.utc) - timedelta(days=7),
            end_date=datetime.now(datetime.timezone.utc),
            total_reviews=10,
            avg_sentiment_score=0.5,
            pain_points=[
                {
                    "title": "Test Pain Point",
                    "description": "This is a test pain point",
                    "priority_score": 0.8,
                    "category": "performance",
                    "sentiment_score": -0.7,
                    "frequency": 3,
                    "examples": ["User reported slow performance", "System lag during peak hours", "Response time needs improvement"]
                }
            ],
            feature_requests=[
                {
                    "title": "Test Feature",
                    "description": "This is a test feature request",
                    "priority_score": 0.6,
                    "category": "usability",
                    "sentiment_score": 0.5,
                    "frequency": 2,
                    "examples": ["Add dark mode option", "Implement keyboard shortcuts"]
                }
            ],
            positive_feedback=[
                {
                    "title": "Test Positive",
                    "description": "This is test positive feedback",
                    "priority_score": 0.9,
                    "category": "user_experience",
                    "sentiment_score": 0.8,
                    "frequency": 4,
                    "examples": ["Great user interface", "Intuitive navigation", "Helpful documentation", "Responsive support"]
                }
            ],
            top_keywords={"test": 5, "feature": 3, "good": 2},
            trend_analysis={
                "daily_metrics": {
                    "2024-05-01": {"sentiment": 0.5, "volume": 2},
                    "2024-05-02": {"sentiment": 0.6, "volume": 3}
                },
                "total_trend": {"direction": "up", "magnitude": 0.1}
            },
            recommendations=["Test recommendation 1", "Test recommendation 2"]
        )

        # 3. Save to database using the service
        summary = await weekly_service.generate_summary(
            source_type="test",
            source_name="test_app",
            start_date=datetime.now(datetime.timezone.utc) - timedelta(days=7),
            end_date=datetime.now(datetime.timezone.utc)
        )
        summary_id = summary.id

        # 4. Test getting the summary
        retrieved_summary = await weekly_service.get_summary_by_id(summary_id)
        if not retrieved_summary:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve test summary"
            )

        # 5. Test getting all summaries
        all_summaries = await weekly_service.get_summaries(source_type="test")
        if not all_summaries:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve all summaries"
            )

        # 6. Test getting priority insights
        insights = await weekly_service.get_priority_insights(source_type="test")
        if not insights:
            raise HTTPException(
                status_code=500,
                detail="Failed to get priority insights"
            )

        # 7. Clean up test data
        collection = get_collection("weekly_summaries")
        await collection.delete_one({"_id": ObjectId(summary_id)})

        # Convert Pydantic models to dictionaries
        retrieved_summary_dict = retrieved_summary.model_dump() if hasattr(retrieved_summary, 'model_dump') else retrieved_summary.dict()
        insights_dict = insights.model_dump() if hasattr(insights, 'model_dump') else insights.dict()

        return {
            "status": "success",
            "message": "All weekly summary functionality tests passed",
            "details": {
                "mongodb_status": status,
                "test_summary_id": summary_id,
                "retrieved_summary": retrieved_summary_dict,
                "total_summaries": len(all_summaries),
                "insights": insights_dict
            }
        }
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )