"""
Dependency injection for FastAPI.
"""

from fastapi import Depends
from app.services.gemini_service import GeminiService
from app.services.analyzer import TextAnalyzer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
_gemini_service = None
_analyzer = None

def get_gemini_service() -> GeminiService:
    """
    Get or create a GeminiService instance.

    Returns:
        GeminiService: The Gemini service instance
    """
    global _gemini_service
    if _gemini_service is None:
        logger.info("Creating new GeminiService instance")
        _gemini_service = GeminiService()
    return _gemini_service

def get_analyzer(gemini_service: GeminiService = Depends(get_gemini_service)) -> TextAnalyzer:
    """
    Get or create a TextAnalyzer instance.

    Args:
        gemini_service: The Gemini service instance

    Returns:
        TextAnalyzer: The text analyzer instance
    """
    global _analyzer
    if _analyzer is None:
        logger.info("Creating new TextAnalyzer instance")
        _analyzer = TextAnalyzer(gemini_service=gemini_service)
    return _analyzer
