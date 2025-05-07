from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging
from pydantic import BaseModel

from ..services.advanced_sentiment import advanced_sentiment_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/sentiment",
    tags=["sentiment"],
    responses={404: {"description": "Not found"}},
)

# Request and response models
class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    sentiment_score: float
    sentiment_label: str
    confidence: float
    is_sarcastic: bool
    sarcasm_confidence: float
    context_analysis: Dict[str, Any]
    aspect_sentiments: List[Dict[str, Any]]

class BatchSentimentRequest(BaseModel):
    texts: List[str]

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]

@router.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment of a single text
    """
    try:
        result = advanced_sentiment_analyzer.analyze_sentiment(request.text)
        return result
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=BatchSentimentResponse)
async def analyze_batch_sentiment(request: BatchSentimentRequest):
    """
    Analyze sentiment of multiple texts using batch processing
    """
    try:
        # Check if batch processing is available
        if hasattr(advanced_sentiment_analyzer, 'analyze_sentiment_batch'):
            logger.info(f"Using batch processing for {len(request.texts)} texts")
            import time
            start_time = time.time()

            # Use batch processing
            results = advanced_sentiment_analyzer.analyze_sentiment_batch(request.texts)

            processing_time = time.time() - start_time
            logger.info(f"Batch sentiment analysis completed in {processing_time:.2f} seconds")
        else:
            # Fall back to individual processing
            logger.info(f"Batch processing not available, processing {len(request.texts)} texts individually")
            results = []
            for text in request.texts:
                result = advanced_sentiment_analyzer.analyze_sentiment(text)
                results.append(result)

        return BatchSentimentResponse(results=results)
    except Exception as e:
        logger.error(f"Error analyzing batch sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
