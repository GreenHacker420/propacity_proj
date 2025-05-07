"""
Routes for Gemini API integration.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gemini", tags=["gemini"])

@router.get("/status")
async def get_gemini_status():
    """
    Get the current status of the Gemini API service.

    This endpoint provides information about the Gemini API service status.
    """
    try:
        # Return a default status since we're in development mode
        return {
            "available": False,
            "model": "gemini-2.0-flash",
            "rate_limited": False,
            "circuit_open": False,
            "using_local_processing": True,
            "rate_limit_reset_in": 0,
            "circuit_reset_in": 0
        }
    except Exception as e:
        logger.error(f"Error getting Gemini service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
