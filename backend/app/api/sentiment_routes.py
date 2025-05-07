from fastapi import APIRouter, HTTPException
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
            raw_results = advanced_sentiment_analyzer.analyze_sentiment_batch(request.texts)

            # Transform raw results into SentimentResponse objects
            results = []
            for result in raw_results:
                try:
                    # Create SentimentResponse object from the result
                    # Handle different result formats
                    if isinstance(result, dict):
                        if "sentiment_score" in result:
                            # Already in the correct format
                            sentiment_response = SentimentResponse(
                                sentiment_score=float(result["sentiment_score"]),
                                sentiment_label=str(result["sentiment_label"]),
                                confidence=float(result["confidence"]),
                                is_sarcastic=bool(result.get("is_sarcastic", False)),
                                sarcasm_confidence=float(result.get("sarcasm_confidence", 0.0)),
                                context_analysis=result.get("context_analysis", {}),
                                aspect_sentiments=result.get("aspect_sentiments", [])
                            )
                        elif "score" in result and "label" in result:
                            # Convert from transformer model format
                            sentiment_response = SentimentResponse(
                                sentiment_score=float(result["score"]),
                                sentiment_label=str(result["label"]),
                                confidence=float(result.get("confidence", 0.5)),
                                is_sarcastic=False,
                                sarcasm_confidence=0.0,
                                context_analysis={},
                                aspect_sentiments=[]
                            )
                        else:
                            # Unknown format, use default
                            logger.warning(f"Unknown result format: {result}")
                            sentiment_response = SentimentResponse(
                                sentiment_score=0.5,
                                sentiment_label="NEUTRAL",
                                confidence=0.0,
                                is_sarcastic=False,
                                sarcasm_confidence=0.0,
                                context_analysis={},
                                aspect_sentiments=[]
                            )
                    else:
                        # Not a dictionary, use default
                        logger.warning(f"Non-dictionary result: {result}")
                        sentiment_response = SentimentResponse(
                            sentiment_score=0.5,
                            sentiment_label="NEUTRAL",
                            confidence=0.0,
                            is_sarcastic=False,
                            sarcasm_confidence=0.0,
                            context_analysis={},
                            aspect_sentiments=[]
                        )

                    results.append(sentiment_response)
                except Exception as conversion_error:
                    logger.error(f"Error converting result {result}: {str(conversion_error)}")
                    # Add a default response
                    results.append(SentimentResponse(
                        sentiment_score=0.5,
                        sentiment_label="NEUTRAL",
                        confidence=0.0,
                        is_sarcastic=False,
                        sarcasm_confidence=0.0,
                        context_analysis={},
                        aspect_sentiments=[]
                    ))

            processing_time = time.time() - start_time
            logger.info(f"Batch sentiment analysis completed in {processing_time:.2f} seconds")
        else:
            # Fall back to individual processing
            logger.info(f"Batch processing not available, processing {len(request.texts)} texts individually")
            results = []
            for text in request.texts:
                result = advanced_sentiment_analyzer.analyze_sentiment(text)
                # Convert to SentimentResponse
                sentiment_response = SentimentResponse(
                    sentiment_score=float(result["sentiment_score"]),
                    sentiment_label=str(result["sentiment_label"]),
                    confidence=float(result["confidence"]),
                    is_sarcastic=bool(result.get("is_sarcastic", False)),
                    sarcasm_confidence=float(result.get("sarcasm_confidence", 0.0)),
                    context_analysis=result.get("context_analysis", {}),
                    aspect_sentiments=result.get("aspect_sentiments", [])
                )
                results.append(sentiment_response)

        return BatchSentimentResponse(results=results)
    except Exception as e:
        logger.error(f"Error analyzing batch sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
