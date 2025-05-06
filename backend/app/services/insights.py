import logging
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
import numpy as np
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsightGenerator:
    """
    Class for generating actionable insights from review data
    """
    
    def __init__(self):
        """
        Initialize the insight generator
        """
        logger.info("Initializing Insight Generator...")
    
    def generate_insights(self, reviews: List[Dict[str, Any]], 
                         aspect_data: Optional[Dict[str, Any]] = None,
                         trend_data: Optional[Dict[str, Any]] = None,
                         cluster_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate actionable insights from review data and analysis results
        
        Args:
            reviews: List of review dictionaries
            aspect_data: Aspect-based sentiment analysis results
            trend_data: Trend analysis results
            cluster_data: Clustering results
            
        Returns:
            Dictionary containing insights
        """
        if not reviews:
            return {
                "key_insights": [],
                "improvement_areas": [],
                "strengths": [],
                "opportunities": []
            }
            
        try:
            insights = {
                "key_insights": [],
                "improvement_areas": [],
                "strengths": [],
                "opportunities": []
            }
            
            # Basic review statistics
            total_reviews = len(reviews)
            
            # Calculate sentiment distribution
            sentiment_counts = Counter(review.get('sentiment_label', 'NEUTRAL') for review in reviews)
            positive_pct = sentiment_counts.get('POSITIVE', 0) / total_reviews * 100 if total_reviews else 0
            negative_pct = sentiment_counts.get('NEGATIVE', 0) / total_reviews * 100 if total_reviews else 0
            neutral_pct = sentiment_counts.get('NEUTRAL', 0) / total_reviews * 100 if total_reviews else 0
            
            # Calculate average rating
            ratings = [review.get('rating', None) for review in reviews]
            ratings = [r for r in ratings if r is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Add basic insights
            insights["key_insights"].append(
                f"Analyzed {total_reviews} reviews with {positive_pct:.1f}% positive, "
                f"{neutral_pct:.1f}% neutral, and {negative_pct:.1f}% negative sentiment."
            )
            
            if avg_rating is not None:
                insights["key_insights"].append(
                    f"Average rating is {avg_rating:.1f} out of 5."
                )
            
            # Add aspect-based insights
            if aspect_data and 'aspects' in aspect_data:
                aspects = aspect_data['aspects']
                
                # Find negative aspects (improvement areas)
                negative_aspects = {
                    aspect: data for aspect, data in aspects.items()
                    if data['sentiment_label'] == 'NEGATIVE' and data['count'] >= 3
                }
                
                # Find positive aspects (strengths)
                positive_aspects = {
                    aspect: data for aspect, data in aspects.items()
                    if data['sentiment_label'] == 'POSITIVE' and data['count'] >= 3
                }
                
                # Add improvement areas
                for aspect, data in sorted(negative_aspects.items(), key=lambda x: x[1]['count'], reverse=True)[:3]:
                    insights["improvement_areas"].append(
                        f"Improve '{aspect}' which was mentioned {data['count']} times with negative sentiment."
                    )
                
                # Add strengths
                for aspect, data in sorted(positive_aspects.items(), key=lambda x: x[1]['count'], reverse=True)[:3]:
                    insights["strengths"].append(
                        f"'{aspect}' is a strength, mentioned {data['count']} times with positive sentiment."
                    )
            
            # Add trend insights
            if trend_data and 'time_metrics' in trend_data and trend_data['time_metrics']:
                metrics = trend_data['time_metrics']
                
                # Check for sentiment trends
                if len(metrics) >= 3:
                    # Get sentiment scores for the last three periods
                    recent_sentiments = [m['avg_sentiment'] for m in metrics[-3:] if m['avg_sentiment'] is not None]
                    
                    if len(recent_sentiments) == 3:
                        # Check for consistent improvement
                        if recent_sentiments[0] < recent_sentiments[1] < recent_sentiments[2]:
                            insights["key_insights"].append(
                                "Sentiment is consistently improving over the last three periods."
                            )
                        # Check for consistent decline
                        elif recent_sentiments[0] > recent_sentiments[1] > recent_sentiments[2]:
                            insights["improvement_areas"].append(
                                "Sentiment is consistently declining over the last three periods. Immediate attention required."
                            )
                
                # Check for volume trends
                if len(metrics) >= 2:
                    # Get review counts for the last two periods
                    recent_volumes = [m['review_count'] for m in metrics[-2:]]
                    
                    # Calculate volume change
                    volume_change = ((recent_volumes[1] - recent_volumes[0]) / recent_volumes[0]) * 100 if recent_volumes[0] else 0
                    
                    if volume_change >= 20:
                        insights["key_insights"].append(
                            f"Review volume increased by {volume_change:.1f}% in the most recent period."
                        )
                    elif volume_change <= -20:
                        insights["key_insights"].append(
                            f"Review volume decreased by {abs(volume_change):.1f}% in the most recent period."
                        )
            
            # Add cluster insights
            if cluster_data and 'clusters' in cluster_data and cluster_data['clusters']:
                clusters = cluster_data['clusters']
                
                # Find largest negative cluster
                negative_clusters = [
                    cluster for cluster in clusters
                    if cluster['dominant_sentiment'] == 'NEGATIVE' and cluster['size'] >= 5
                ]
                
                if negative_clusters:
                    largest_negative = max(negative_clusters, key=lambda x: x['size'])
                    insights["improvement_areas"].append(
                        f"Address feedback cluster about '{', '.join(largest_negative['top_terms'][:3])}' "
                        f"with {largest_negative['size']} negative reviews."
                    )
                
                # Find emerging topics (smaller clusters with strong sentiment)
                small_clusters = [
                    cluster for cluster in clusters
                    if 3 <= cluster['size'] < 10 and cluster['dominant_sentiment'] != 'NEUTRAL'
                ]
                
                for cluster in small_clusters[:2]:
                    sentiment = "positive" if cluster['dominant_sentiment'] == 'POSITIVE' else "negative"
                    insights["opportunities"].append(
                        f"Emerging topic: '{', '.join(cluster['top_terms'][:3])}' with {sentiment} sentiment "
                        f"in {cluster['size']} reviews."
                    )
            
            # Generate additional insights based on keywords
            keyword_counter = Counter()
            for review in reviews:
                keywords = review.get('keywords', [])
                keyword_counter.update(keywords)
            
            top_keywords = keyword_counter.most_common(5)
            if top_keywords:
                insights["key_insights"].append(
                    f"Most frequent keywords: {', '.join(kw for kw, _ in top_keywords)}."
                )
            
            # Add recommendations if we don't have enough
            if len(insights["improvement_areas"]) < 2:
                # Find reviews with lowest sentiment scores
                negative_reviews = sorted(reviews, key=lambda x: x.get('sentiment_score', 0.5))[:5]
                if negative_reviews:
                    # Extract common words from negative reviews
                    negative_text = ' '.join(review.get('text', '') for review in negative_reviews)
                    words = re.findall(r'\b\w+\b', negative_text.lower())
                    word_counter = Counter(words)
                    
                    # Filter out common words
                    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                                   'be', 'been', 'being', 'to', 'of', 'for', 'with', 'that', 'this',
                                   'these', 'those', 'it', 'its', 'in', 'on', 'at', 'by', 'from'}
                    
                    for word in common_words:
                        word_counter.pop(word, None)
                    
                    top_negative_words = word_counter.most_common(3)
                    if top_negative_words:
                        insights["improvement_areas"].append(
                            f"Consider addressing issues related to: {', '.join(word for word, _ in top_negative_words)}."
                        )
            
            if len(insights["strengths"]) < 2:
                # Find reviews with highest sentiment scores
                positive_reviews = sorted(reviews, key=lambda x: x.get('sentiment_score', 0.5), reverse=True)[:5]
                if positive_reviews:
                    # Extract common words from positive reviews
                    positive_text = ' '.join(review.get('text', '') for review in positive_reviews)
                    words = re.findall(r'\b\w+\b', positive_text.lower())
                    word_counter = Counter(words)
                    
                    # Filter out common words
                    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                                   'be', 'been', 'being', 'to', 'of', 'for', 'with', 'that', 'this',
                                   'these', 'those', 'it', 'its', 'in', 'on', 'at', 'by', 'from'}
                    
                    for word in common_words:
                        word_counter.pop(word, None)
                    
                    top_positive_words = word_counter.most_common(3)
                    if top_positive_words:
                        insights["strengths"].append(
                            f"Continue to focus on strengths related to: {', '.join(word for word, _ in top_positive_words)}."
                        )
            
            # Add opportunities if we don't have enough
            if len(insights["opportunities"]) < 2:
                insights["opportunities"].append(
                    "Consider implementing a customer feedback loop to address recurring issues promptly."
                )
                insights["opportunities"].append(
                    "Analyze competitor reviews to identify potential feature gaps and opportunities."
                )
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                "key_insights": ["Error generating insights. Please try again."],
                "improvement_areas": [],
                "strengths": [],
                "opportunities": []
            }
