from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from ..models.weekly_summary import WeeklySummaryCreate, WeeklySummaryResponse, PriorityItem, PriorityInsights
from ..mongodb import get_collection
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..services.text_classifier import TextClassifier
from bson.objectid import ObjectId
import logging
import random

logger = logging.getLogger(__name__)

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

        # Build the query
        query = {
            "source_type": source_type,
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        # Only add source_name to query if it's not None and not the same as source_type
        if source_name and source_name != source_type:
            query["source_name"] = source_name

        # Use find method without await, then to_list with await
        cursor = reviews_collection.find(query)
        reviews = await cursor.to_list(length=None)

        logger.info(f"Found {len(reviews)} reviews for query: {query}")

        if not reviews:
            # Generate mock data for testing if no reviews found
            logger.warning("No reviews found for the specified date range. Generating mock data.")
            reviews = self._generate_mock_reviews(source_type, 10)

        # Analyze sentiment and classify feedback
        pain_points = []
        feature_requests = []
        positive_feedback = []
        total_sentiment = 0
        keyword_freq: Dict[str, int] = {}

        # Process reviews in batches to avoid too many concurrent requests
        for review in reviews:
            try:
                # Analyze sentiment - use synchronous call
                sentiment_score = await self.sentiment_analyzer.analyze_sentiment(review["text"])
                total_sentiment += sentiment_score

                # Classify feedback - use synchronous call
                feedback_type = await self.text_classifier.classify_feedback(review["text"])

                # Extract keywords - use synchronous call
                keywords = await self.text_classifier.extract_keywords(review["text"])
                for keyword in keywords:
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            except Exception as e:
                logger.error(f"Error processing review: {str(e)}")
                # Use default values if processing fails
                sentiment_score = 0.0
                feedback_type = "positive_feedback"
                keywords = []

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
        trend_analysis = self._analyze_trends(reviews)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            pain_points, feature_requests, positive_feedback, trend_analysis
        )

        # Convert PriorityItem objects to dictionaries
        pain_points_dicts = []
        for item in sorted(pain_points, key=lambda x: x.priority_score, reverse=True)[:5]:
            if hasattr(item, 'model_dump'):
                pain_points_dicts.append(item.model_dump())
            elif hasattr(item, 'dict'):
                pain_points_dicts.append(item.dict())
            else:
                logger.warning(f"Skipping pain point that can't be converted to dict: {type(item)}")

        feature_requests_dicts = []
        for item in sorted(feature_requests, key=lambda x: x.priority_score, reverse=True)[:5]:
            if hasattr(item, 'model_dump'):
                feature_requests_dicts.append(item.model_dump())
            elif hasattr(item, 'dict'):
                feature_requests_dicts.append(item.dict())
            else:
                logger.warning(f"Skipping feature request that can't be converted to dict: {type(item)}")

        positive_feedback_dicts = []
        for item in sorted(positive_feedback, key=lambda x: x.priority_score, reverse=True)[:5]:
            if hasattr(item, 'model_dump'):
                positive_feedback_dicts.append(item.model_dump())
            elif hasattr(item, 'dict'):
                positive_feedback_dicts.append(item.dict())
            else:
                logger.warning(f"Skipping positive feedback that can't be converted to dict: {type(item)}")

        # Create weekly summary
        summary = WeeklySummaryCreate(
            source_type=source_type,
            source_name=source_name,
            start_date=start_date,
            end_date=end_date,
            total_reviews=len(reviews),
            avg_sentiment_score=avg_sentiment,
            pain_points=pain_points_dicts,
            feature_requests=feature_requests_dicts,
            positive_feedback=positive_feedback_dicts,
            top_keywords=dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            trend_analysis=trend_analysis,
            recommendations=recommendations
        )

        # Save to database
        summary_dict = summary.model_dump() if hasattr(summary, 'model_dump') else summary.dict()
        result = await self.collection.insert_one(summary_dict)
        summary_dict["_id"] = str(result.inserted_id)
        summary_dict["created_at"] = datetime.now(timezone.utc)
        summary_dict["user_id"] = user_id

        return WeeklySummaryResponse(**summary_dict)

    async def get_priority_insights(
        self,
        source_type: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 7
    ) -> PriorityInsights:
        """Get priority insights from recent feedback"""
        try:
            # Get recent summaries
            query = {}
            if source_type:
                query["source_type"] = source_type
            if user_id:
                query["user_id"] = user_id

            query["created_at"] = {
                "$gte": datetime.now(timezone.utc) - timedelta(days=days)
            }

            # Use find method without await
            cursor = self.collection.find(query)
            # Use to_list with await
            summaries = await cursor.to_list(length=None)

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
                summary_dict = summary
                if "pain_points" in summary_dict:
                    # Convert each pain point to a dictionary if it's not already
                    pain_points_list = []
                    for item in summary_dict["pain_points"]:
                        if isinstance(item, dict):
                            pain_points_list.append(item)
                        else:
                            # This is likely a Pydantic model, convert to dict
                            try:
                                if hasattr(item, 'model_dump'):
                                    pain_points_list.append(item.model_dump())
                                elif hasattr(item, 'dict'):
                                    pain_points_list.append(item.dict())
                                else:
                                    # Skip items we can't convert
                                    logger.warning(f"Skipping pain point that can't be converted to dict: {type(item)}")
                            except Exception as e:
                                logger.warning(f"Error converting pain point to dict: {str(e)}")
                    high_priority_items.extend(pain_points_list)

                if "feature_requests" in summary_dict:
                    # Convert each feature request to a dictionary if it's not already
                    feature_requests_list = []
                    for item in summary_dict["feature_requests"]:
                        if isinstance(item, dict):
                            feature_requests_list.append(item)
                        else:
                            # This is likely a Pydantic model, convert to dict
                            try:
                                if hasattr(item, 'model_dump'):
                                    feature_requests_list.append(item.model_dump())
                                elif hasattr(item, 'dict'):
                                    feature_requests_list.append(item.dict())
                                else:
                                    # Skip items we can't convert
                                    logger.warning(f"Skipping feature request that can't be converted to dict: {type(item)}")
                            except Exception as e:
                                logger.warning(f"Error converting feature request to dict: {str(e)}")
                    high_priority_items.extend(feature_requests_list)

                # Analyze trends
                if "top_keywords" in summary_dict:
                    trending_topics.extend([
                        {"topic": k, "count": v}
                        for k, v in summary_dict["top_keywords"].items()
                    ])

                # Track sentiment trends
                if "source_name" in summary_dict and "avg_sentiment_score" in summary_dict:
                    sentiment_trends[summary_dict["source_name"]] = summary_dict["avg_sentiment_score"]

                # Extract recommendations
                if "recommendations" in summary_dict:
                    for rec in summary_dict["recommendations"]:
                        if isinstance(rec, str):
                            if "risk" in rec.lower():
                                risk_areas.add(rec)
                            elif "opportunity" in rec.lower():
                                opportunity_areas.add(rec)
                            else:
                                action_items.add(rec)

            # Sort and limit high priority items
            sorted_high_priority = []
            if high_priority_items:
                # Make sure all items are dictionaries
                dict_items = []
                for item in high_priority_items:
                    if isinstance(item, dict):
                        dict_items.append(item)
                    else:
                        try:
                            if hasattr(item, 'model_dump'):
                                dict_items.append(item.model_dump())
                            elif hasattr(item, 'dict'):
                                dict_items.append(item.dict())
                        except Exception as e:
                            logger.warning(f"Error converting item to dict: {str(e)}")

                # Sort the dictionary items
                sorted_high_priority = sorted(
                    dict_items,
                    key=lambda x: x.get("priority_score", 0),
                    reverse=True
                )[:10]

            # Sort and limit trending topics
            sorted_trending = []
            if trending_topics:
                # Make sure all items are dictionaries
                dict_topics = []
                for topic in trending_topics:
                    if isinstance(topic, dict):
                        dict_topics.append(topic)
                    else:
                        try:
                            if hasattr(topic, 'model_dump'):
                                dict_topics.append(topic.model_dump())
                            elif hasattr(topic, 'dict'):
                                dict_topics.append(topic.dict())
                        except Exception as e:
                            logger.warning(f"Error converting topic to dict: {str(e)}")

                # Sort the dictionary topics
                sorted_trending = sorted(
                    dict_topics,
                    key=lambda x: x.get("count", 0),
                    reverse=True
                )[:5]

            return PriorityInsights(
                high_priority_items=sorted_high_priority,
                trending_topics=sorted_trending,
                sentiment_trends=sentiment_trends,
                action_items=list(action_items),
                risk_areas=list(risk_areas),
                opportunity_areas=list(opportunity_areas)
            )
        except Exception as e:
            logger.error(f"Error getting priority insights: {str(e)}")
            raise

    def _calculate_priority_score(self, sentiment_score: float, feedback_type: str) -> float:
        """Calculate priority score based on sentiment and feedback type"""
        base_score = abs(sentiment_score)  # Higher absolute sentiment means higher priority

        # Adjust based on feedback type
        if feedback_type == "pain_point":
            base_score *= 1.5  # Pain points get higher priority
        elif feedback_type == "feature_request":
            base_score *= 1.2  # Feature requests get medium priority

        return min(base_score, 1.0)  # Normalize to 0-1 range

    def _analyze_trends(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in the reviews"""
        # Group reviews by day
        daily_reviews = {}
        for review in reviews:
            try:
                # Handle different date formats
                if isinstance(review["created_at"], datetime):
                    day = review["created_at"].date()
                elif isinstance(review["created_at"], str):
                    day = datetime.fromisoformat(review["created_at"]).date()
                else:
                    # Default to today if date can't be parsed
                    day = datetime.now(timezone.utc).date()

                if day not in daily_reviews:
                    daily_reviews[day] = []
                daily_reviews[day].append(review)
            except Exception as e:
                logger.error(f"Error processing review date: {str(e)}")
                # Skip this review if we can't process the date

        # Calculate daily metrics
        daily_metrics = {}
        for day, day_reviews in daily_reviews.items():
            try:
                # Get sentiment score safely
                sentiment_scores = []
                for r in day_reviews:
                    if "sentiment_score" in r and r["sentiment_score"] is not None:
                        sentiment_scores.append(r["sentiment_score"])

                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

                # Count feedback types safely
                pain_points = 0
                feature_requests = 0
                positive_feedback = 0

                for r in day_reviews:
                    if "feedback_type" in r:
                        if r["feedback_type"] == "pain_point":
                            pain_points += 1
                        elif r["feedback_type"] == "feature_request":
                            feature_requests += 1
                        elif r["feedback_type"] == "positive_feedback":
                            positive_feedback += 1

                daily_metrics[str(day)] = {
                    "count": len(day_reviews),
                    "avg_sentiment": avg_sentiment,
                    "pain_points": pain_points,
                    "feature_requests": feature_requests,
                    "positive_feedback": positive_feedback
                }
            except Exception as e:
                logger.error(f"Error calculating metrics for day {day}: {str(e)}")
                # Skip this day if we can't calculate metrics

        # Handle the case where there's only one day of data
        if len(daily_metrics) <= 1:
            return {
                "daily_metrics": daily_metrics,
                "total_trend": {
                    "direction": "neutral",
                    "magnitude": 0.0
                }
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

    def _generate_recommendations(
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

    async def get_summary_by_id(self, summary_id: str) -> Optional[WeeklySummaryResponse]:
        """Get a specific weekly summary by ID"""
        try:
            # Use find_one with await
            summary = await self.collection.find_one({"_id": ObjectId(summary_id)})
            if summary:
                summary["_id"] = str(summary["_id"])
                return WeeklySummaryResponse(**summary)
            return None
        except Exception as e:
            logger.error(f"Error getting summary by ID: {str(e)}")
            raise

    async def get_summaries(
        self,
        source_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[WeeklySummaryResponse]:
        """Get all weekly summaries, optionally filtered by source type and user ID"""
        try:
            query = {}
            if source_type:
                query["source_type"] = source_type
            if user_id:
                query["user_id"] = user_id

            # Use find method without await
            cursor = self.collection.find(query)
            # Use to_list with await
            summaries = await cursor.to_list(length=None)

            # Convert ObjectId to string and create response objects
            for summary in summaries:
                summary["_id"] = str(summary["_id"])

            return [WeeklySummaryResponse(**summary) for summary in summaries]
        except Exception as e:
            logger.error(f"Error getting summaries: {str(e)}")
            raise

    def _generate_mock_reviews(self, source_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Generate mock reviews for testing when no real reviews are available"""
        logger.info(f"Generating {count} mock reviews for source_type: {source_type}")

        mock_texts = [
            "I love this app! It's so intuitive and easy to use.",
            "The app keeps crashing whenever I try to upload photos. Please fix this!",
            "Would love to have dark mode in the next update!",
            "Login with Google fails randomly. Very frustrating.",
            "Please add offline mode for travel. It would be so useful.",
            "Best app ever - beautiful UI and fast loading times.",
            "The search function is too slow. Takes forever to find anything.",
            "Can you add more customization options? Would make it perfect!",
            "Notifications are not working properly on my device.",
            "Love the new update! Much faster now.",
            "This app is a game changer for my productivity.",
            "The UI is confusing and hard to navigate.",
            "Wish there was a way to organize items into folders.",
            "App crashes every time I try to save my progress.",
            "Great customer support! They resolved my issue quickly."
        ]

        mock_reviews = []
        for i in range(min(count, len(mock_texts))):
            # Create a mock review with all required fields
            sentiment_score = random.uniform(-0.9, 0.9)  # Allow negative sentiment scores

            # Determine feedback type based on sentiment
            if sentiment_score < -0.3:
                feedback_type = "pain_point"
            elif sentiment_score < 0.3:
                feedback_type = "feature_request"
            else:
                feedback_type = "positive_feedback"

            mock_review = {
                "text": mock_texts[i],
                "source_type": source_type,
                "source_name": source_type,
                "created_at": datetime.now(timezone.utc) - timedelta(days=random.randint(0, 6)),
                "sentiment_score": sentiment_score,
                "sentiment_label": "POSITIVE" if sentiment_score > 0 else "NEGATIVE",
                "category": feedback_type,
                "feedback_type": feedback_type,
                "keywords": ["app", "feature", "update"]
            }
            mock_reviews.append(mock_review)

        return mock_reviews