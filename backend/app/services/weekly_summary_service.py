from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from ..models.weekly_summary import WeeklySummaryCreate, WeeklySummaryResponse, PriorityItem, PriorityInsights
from ..db.mongodb import get_collection
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..services.text_classifier import TextClassifier

class WeeklySummaryService:
    def __init__(self):
        self.collection: AsyncIOMotorCollection = get_collection("weekly_summaries")
        self.sentiment_analyzer = SentimentAnalyzer()
        self.text_classifier = TextClassifier()

    async def generate_summary(
        self,
        source_type: str,
        source_name: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> WeeklySummaryResponse:
        """Generate a weekly summary for the specified source and date range"""
        # Get reviews from the specified date range
        reviews_collection = get_collection("reviews")
        reviews = await reviews_collection.find({
            "source_type": source_type,
            "source_name": source_name,
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).to_list(length=None)

        if not reviews:
            raise ValueError("No reviews found for the specified date range")

        # Analyze sentiment and classify feedback
        pain_points = []
        feature_requests = []
        positive_feedback = []
        total_sentiment = 0
        keyword_freq: Dict[str, int] = {}

        for review in reviews:
            # Analyze sentiment
            sentiment_score = await self.sentiment_analyzer.analyze_sentiment(review["text"])
            total_sentiment += sentiment_score

            # Classify feedback
            feedback_type = await self.text_classifier.classify_feedback(review["text"])
            
            # Extract keywords
            keywords = await self.text_classifier.extract_keywords(review["text"])
            for keyword in keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

            # Create priority item
            priority_item = PriorityItem(
                title=review["text"][:50] + "...",
                description=review["text"],
                priority_score=self._calculate_priority_score(sentiment_score, feedback_type),
                category=feedback_type,
                sentiment_score=sentiment_score,
                frequency=1,
                examples=[review["text"]]
            )

            # Add to appropriate list
            if feedback_type == "pain_point":
                pain_points.append(priority_item)
            elif feedback_type == "feature_request":
                feature_requests.append(priority_item)
            else:
                positive_feedback.append(priority_item)

        # Calculate average sentiment
        avg_sentiment = total_sentiment / len(reviews)

        # Generate trend analysis
        trend_analysis = await self._analyze_trends(reviews)

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            pain_points, feature_requests, positive_feedback, trend_analysis
        )

        # Create weekly summary
        summary = WeeklySummaryCreate(
            source_type=source_type,
            source_name=source_name,
            start_date=start_date,
            end_date=end_date,
            total_reviews=len(reviews),
            avg_sentiment_score=avg_sentiment,
            pain_points=sorted(pain_points, key=lambda x: x.priority_score, reverse=True)[:5],
            feature_requests=sorted(feature_requests, key=lambda x: x.priority_score, reverse=True)[:5],
            positive_feedback=sorted(positive_feedback, key=lambda x: x.priority_score, reverse=True)[:5],
            top_keywords=dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            trend_analysis=trend_analysis,
            recommendations=recommendations
        )

        # Save to database
        result = await self.collection.insert_one(summary.dict())
        summary_dict = summary.dict()
        summary_dict["_id"] = str(result.inserted_id)
        summary_dict["created_at"] = datetime.utcnow()
        summary_dict["user_id"] = user_id

        return WeeklySummaryResponse(**summary_dict)

    async def get_priority_insights(
        self,
        source_type: Optional[str] = None,
        days: int = 7
    ) -> PriorityInsights:
        """Get priority insights from recent feedback"""
        # Get recent summaries
        query = {}
        if source_type:
            query["source_type"] = source_type
        
        query["created_at"] = {
            "$gte": datetime.utcnow() - timedelta(days=days)
        }

        summaries = await self.collection.find(query).to_list(length=None)

        if not summaries:
            raise ValueError("No summaries found for the specified criteria")

        # Aggregate high priority items
        high_priority_items = []
        trending_topics = []
        sentiment_trends = {}
        action_items = set()
        risk_areas = set()
        opportunity_areas = set()

        for summary in summaries:
            # Collect high priority items
            high_priority_items.extend(summary["pain_points"])
            high_priority_items.extend(summary["feature_requests"])

            # Analyze trends
            trending_topics.extend([
                {"topic": k, "count": v}
                for k, v in summary["top_keywords"].items()
            ])

            # Track sentiment trends
            sentiment_trends[summary["source_name"]] = summary["avg_sentiment_score"]

            # Extract recommendations
            for rec in summary["recommendations"]:
                if "risk" in rec.lower():
                    risk_areas.add(rec)
                elif "opportunity" in rec.lower():
                    opportunity_areas.add(rec)
                else:
                    action_items.add(rec)

        return PriorityInsights(
            high_priority_items=sorted(high_priority_items, key=lambda x: x["priority_score"], reverse=True)[:10],
            trending_topics=sorted(trending_topics, key=lambda x: x["count"], reverse=True)[:5],
            sentiment_trends=sentiment_trends,
            action_items=list(action_items),
            risk_areas=list(risk_areas),
            opportunity_areas=list(opportunity_areas)
        )

    def _calculate_priority_score(self, sentiment_score: float, feedback_type: str) -> float:
        """Calculate priority score based on sentiment and feedback type"""
        base_score = abs(sentiment_score)  # Higher absolute sentiment means higher priority
        
        # Adjust based on feedback type
        if feedback_type == "pain_point":
            base_score *= 1.5  # Pain points get higher priority
        elif feedback_type == "feature_request":
            base_score *= 1.2  # Feature requests get medium priority
        
        return min(base_score, 1.0)  # Normalize to 0-1 range

    async def _analyze_trends(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in the reviews"""
        # Group reviews by day
        daily_reviews = {}
        for review in reviews:
            day = review["created_at"].date()
            if day not in daily_reviews:
                daily_reviews[day] = []
            daily_reviews[day].append(review)

        # Calculate daily metrics
        daily_metrics = {}
        for day, day_reviews in daily_reviews.items():
            daily_metrics[str(day)] = {
                "count": len(day_reviews),
                "avg_sentiment": sum(r["sentiment_score"] for r in day_reviews) / len(day_reviews),
                "pain_points": sum(1 for r in day_reviews if r["feedback_type"] == "pain_point"),
                "feature_requests": sum(1 for r in day_reviews if r["feedback_type"] == "feature_request"),
                "positive_feedback": sum(1 for r in day_reviews if r["feedback_type"] == "positive_feedback")
            }

        return {
            "daily_metrics": daily_metrics,
            "total_trend": {
                "direction": "up" if daily_metrics[max(daily_metrics.keys())]["avg_sentiment"] >
                                daily_metrics[min(daily_metrics.keys())]["avg_sentiment"] else "down",
                "magnitude": abs(daily_metrics[max(daily_metrics.keys())]["avg_sentiment"] -
                               daily_metrics[min(daily_metrics.keys())]["avg_sentiment"])
            }
        }

    async def _generate_recommendations(
        self,
        pain_points: List[PriorityItem],
        feature_requests: List[PriorityItem],
        positive_feedback: List[PriorityItem],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on the analysis"""
        recommendations = []

        # Analyze pain points
        if pain_points:
            top_pain = pain_points[0]
            recommendations.append(
                f"Address the top pain point: {top_pain.title} "
                f"(Priority Score: {top_pain.priority_score:.2f})"
            )

        # Analyze feature requests
        if feature_requests:
            top_request = feature_requests[0]
            recommendations.append(
                f"Consider implementing the most requested feature: {top_request.title} "
                f"(Priority Score: {top_request.priority_score:.2f})"
            )

        # Analyze trends
        if trend_analysis["total_trend"]["direction"] == "down":
            recommendations.append(
                f"Warning: Sentiment trend is declining. "
                f"Magnitude of change: {trend_analysis['total_trend']['magnitude']:.2f}"
            )

        # Add opportunity areas
        if positive_feedback:
            top_positive = positive_feedback[0]
            recommendations.append(
                f"Opportunity: Leverage the positive feedback about {top_positive.title} "
                f"to improve other areas"
            )

        return recommendations 