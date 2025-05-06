from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from sqlalchemy.orm import Session

from .models import (
    ReviewResponse, 
    AdvancedAnalysisRequest, 
    AdvancedAnalysisResponse,
    EntityAnalysisResponse,
    TopicModelingResponse,
    AspectAnalysisResponse,
    EmotionAnalysisResponse,
    TrendAnalysisResponse,
    ClusteringResponse,
    InsightsResponse,
    LanguageAnalysisResponse
)
from ..services.ner import NamedEntityRecognizer
from ..services.topic_modeling import TopicModeler
from ..services.aspect_sentiment import AspectSentimentAnalyzer
from ..services.emotion_detection import EmotionDetector
from ..services.trend_analysis import TrendAnalyzer
from ..services.clustering import FeedbackClusterer
from ..services.insights import InsightGenerator
from ..services.language import LanguageProcessor
from ..database import get_db
from ..auth.security import get_current_active_user
from ..models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
ner = NamedEntityRecognizer()
topic_modeler = TopicModeler()
aspect_analyzer = AspectSentimentAnalyzer()
emotion_detector = EmotionDetector()
trend_analyzer = TrendAnalyzer()
clusterer = FeedbackClusterer()
insight_generator = InsightGenerator()
language_processor = LanguageProcessor()

router = APIRouter(prefix="/advanced", tags=["advanced analysis"])

@router.post("/analyze", response_model=AdvancedAnalysisResponse)
async def advanced_analysis(
    request: AdvancedAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform advanced analysis on review data
    
    This endpoint provides comprehensive analysis including:
    - Named Entity Recognition
    - Topic Modeling
    - Aspect-Based Sentiment Analysis
    - Emotion Detection
    - Trend Analysis
    - Feedback Clustering
    - Automated Insights Generation
    - Multi-language Support
    
    You can specify which analyses to perform using the analysis_types parameter.
    """
    try:
        if not request.reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")
            
        logger.info(f"Performing advanced analysis on {len(request.reviews)} reviews")
        
        # Determine which analyses to perform
        analysis_types = request.analysis_types
        perform_all = "all" in analysis_types
        
        # Process multilingual reviews if needed
        if perform_all or "languages" in analysis_types:
            reviews = language_processor.process_multilingual_reviews(
                request.reviews, 
                target_lang=request.target_language
            )
        else:
            reviews = request.reviews
            
        # Extract texts for analysis
        texts = [review.text for review in reviews if review.text]
        
        if not texts:
            raise HTTPException(status_code=400, detail="No valid text content in reviews")
        
        # Initialize response
        response = AdvancedAnalysisResponse()
        
        # Perform entity analysis
        if perform_all or "entities" in analysis_types:
            logger.info("Performing entity analysis")
            entities = []
            for text in texts[:100]:  # Limit to first 100 texts for performance
                entities.extend(ner.extract_entities(text))
                
            entity_counts = ner.get_entity_counts(texts)
            product_mentions = ner.extract_product_mentions(texts)
            
            response.entity_analysis = EntityAnalysisResponse(
                entities=entities,
                entity_counts=entity_counts,
                product_mentions=product_mentions
            )
        
        # Perform topic modeling
        if perform_all or "topics" in analysis_types:
            logger.info("Performing topic modeling")
            topic_results = topic_modeler.extract_topics(
                texts, 
                n_topics=request.n_topics
            )
            
            response.topic_modeling = TopicModelingResponse(
                topics=topic_results["topics"],
                topic_distribution=topic_results["topic_distribution"]
            )
        
        # Perform aspect-based sentiment analysis
        if perform_all or "aspects" in analysis_types:
            logger.info("Performing aspect-based sentiment analysis")
            aspect_results = aspect_analyzer.analyze_aspects(texts)
            
            response.aspect_analysis = AspectAnalysisResponse(
                aspects=aspect_results["aspects"],
                visualization=aspect_results["visualization"]
            )
        
        # Perform emotion analysis
        if perform_all or "emotions" in analysis_types:
            logger.info("Performing emotion analysis")
            emotion_results = emotion_detector.analyze_emotions(texts)
            
            response.emotion_analysis = EmotionAnalysisResponse(
                emotions=emotion_results["emotions"],
                percentages=emotion_results["percentages"],
                visualization=emotion_results["visualization"]
            )
        
        # Perform trend analysis
        if perform_all or "trends" in analysis_types:
            logger.info("Performing trend analysis")
            trend_results = trend_analyzer.analyze_trends(
                reviews, 
                time_period=request.time_period
            )
            
            response.trend_analysis = TrendAnalysisResponse(
                time_metrics=trend_results.get("time_metrics", []),
                sentiment_trend=trend_results.get("sentiment_trend"),
                rating_trend=trend_results.get("rating_trend"),
                volume_trend=trend_results.get("volume_trend")
            )
        
        # Perform clustering
        if perform_all or "clusters" in analysis_types:
            logger.info("Performing feedback clustering")
            cluster_results = clusterer.cluster_feedback(
                reviews, 
                n_clusters=request.n_clusters
            )
            
            response.clustering = ClusteringResponse(
                clusters=cluster_results["clusters"],
                visualization=cluster_results["visualization"]
            )
        
        # Generate insights
        if perform_all or "insights" in analysis_types:
            logger.info("Generating insights")
            insights = insight_generator.generate_insights(
                reviews,
                aspect_data=response.aspect_analysis.dict() if response.aspect_analysis else None,
                trend_data=response.trend_analysis.dict() if response.trend_analysis else None,
                cluster_data=response.clustering.dict() if response.clustering else None
            )
            
            response.insights = InsightsResponse(**insights)
        
        # Perform language analysis
        if perform_all or "languages" in analysis_types:
            logger.info("Performing language analysis")
            language_distribution = language_processor.get_language_distribution(reviews)
            language_names = {
                lang: language_processor.get_language_name(lang)
                for lang in language_distribution.keys()
            }
            
            response.language_analysis = LanguageAnalysisResponse(
                language_distribution=language_distribution,
                language_names=language_names
            )
        
        return response
    except Exception as e:
        logger.error(f"Error in advanced analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
