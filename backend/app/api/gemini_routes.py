"""
Routes for Gemini API integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from app.api.gemini_models import GeminiInsightRequest
from app.services.gemini_service import GeminiService
from app.dependencies import get_gemini_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gemini", tags=["gemini"])

@router.get("/status")
async def get_gemini_status(gemini_service: GeminiService = Depends(get_gemini_service)):
    """
    Get the current status of the Gemini API service.

    This endpoint provides information about the Gemini API service status.
    """
    try:
        # Get the actual status from the Gemini service
        return {
            "available": gemini_service.available,
            "model": gemini_service.model_name,
            "rate_limited": gemini_service.rate_limited,
            "circuit_open": gemini_service.circuit_open,
            "using_local_processing": not gemini_service.available or gemini_service.circuit_open or gemini_service.rate_limited,
            "rate_limit_reset_in": int(max(0, gemini_service.rate_limit_reset_time - gemini_service._get_current_time())) if gemini_service.rate_limited else 0,
            "circuit_reset_in": int(max(0, gemini_service.circuit_reset_time - gemini_service._get_current_time())) if gemini_service.circuit_open else 0
        }
    except Exception as e:
        logger.error(f"Error getting Gemini service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insights")
async def extract_insights(request: GeminiInsightRequest, gemini_service: GeminiService = Depends(get_gemini_service)):
    """
    Extract insights from a collection of reviews using Gemini API.

    This endpoint analyzes the provided reviews and extracts key insights including:
    - Summary of the overall feedback
    - Key points from the reviews
    - Pain points mentioned by users
    - Feature requests identified in the reviews
    - Positive feedback from users

    Returns a structured analysis that can be used to inform product decisions.
    """
    try:
        if not request.reviews:
            raise HTTPException(status_code=400, detail="No reviews provided for analysis")

        # Extract insights using the Gemini service
        insights = gemini_service.extract_insights(request.reviews)

        # Return the insights
        return insights
    except Exception as e:
        logger.error(f"Error extracting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
