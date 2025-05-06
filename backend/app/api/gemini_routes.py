"""
Routes for Gemini API integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
import time
from sqlalchemy.orm import Session

from .gemini_models import (
    GeminiSentimentRequest,
    GeminiSentimentResponse,
    GeminiBatchRequest,
    GeminiBatchResponse,
    GeminiInsightRequest,
    GeminiInsightResponse
)
from ..services.gemini_service import GeminiService
from ..database import get_db
from ..auth.security import get_current_active_user
from ..models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini service
gemini_service = GeminiService()

router = APIRouter(prefix="/gemini", tags=["gemini"])

@router.post("/sentiment", response_model=GeminiSentimentResponse)
async def analyze_sentiment(
    request: GeminiSentimentRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze sentiment of text using Google's Gemini API.
    
    This endpoint provides fast sentiment analysis using Gemini's advanced language models.
    """
    try:
        if not gemini_service.available:
            raise HTTPException(status_code=503, detail="Gemini API service is not available")
            
        start_time = time.time()
        result = gemini_service.analyze_sentiment(request.text)
        processing_time = time.time() - start_time
        
        # Add processing time to the result
        result["processing_time"] = processing_time
        
        return result
    except Exception as e:
        logger.error(f"Error in Gemini sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=GeminiBatchResponse)
async def analyze_batch(
    request: GeminiBatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Analyze multiple texts in batch using Google's Gemini API.
    
    This endpoint provides fast batch processing for multiple texts.
    """
    try:
        if not gemini_service.available:
            raise HTTPException(status_code=503, detail="Gemini API service is not available")
            
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided")
            
        start_time = time.time()
        results = gemini_service.analyze_reviews(request.texts)
        processing_time = time.time() - start_time
        
        # Create response with processing time
        response = {
            "results": results,
            "processing_time": processing_time
        }
        
        return response
    except Exception as e:
        logger.error(f"Error in Gemini batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insights", response_model=GeminiInsightResponse)
async def extract_insights(
    request: GeminiInsightRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract insights from a collection of reviews using Google's Gemini API.
    
    This endpoint provides advanced analysis to extract key insights, pain points,
    feature requests, and positive aspects from a collection of reviews.
    """
    try:
        if not gemini_service.available:
            raise HTTPException(status_code=503, detail="Gemini API service is not available")
            
        if not request.reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")
            
        start_time = time.time()
        result = gemini_service.extract_insights(request.reviews)
        processing_time = time.time() - start_time
        
        # Add processing time to the result
        result["processing_time"] = processing_time
        
        return result
    except Exception as e:
        logger.error(f"Error in Gemini insight extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
