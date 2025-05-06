from transformers import pipeline
from ..api.models import Review, AnalysisResults

sentiment_analyzer = pipeline("sentiment-analysis")

async def analyze_sentiment(reviews: list[Review]) -> AnalysisResults:
    # Analyze sentiment for each review
    results = sentiment_analyzer([r.text for r in reviews])
    sentiment_scores = [
        1.0 if r['label'] == 'POSITIVE' else 0.0 
        for r in results
    ]
    
    # Calculate average rating
    ratings = [r.rating for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    
    return AnalysisResults(
        sentiment_scores=sentiment_scores,
        average_rating=avg_rating,
        review_count=len(reviews)
    ) 