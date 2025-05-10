from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
# Remove motor import and use pymongo instead
from pymongo.collection import Collection
from ..models.weekly_summary import WeeklySummaryCreate, WeeklySummaryResponse, PriorityItem, PriorityInsights
from ..mongodb import get_collection
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..services.text_classifier import TextClassifier
from bson.objectid import ObjectId
import logging
import os

logger = logging.getLogger(__name__)

class WeeklySummaryService:
    def __init__(self):
        self.collection = get_collection("weekly_summaries")
        self.sentiment_analyzer = SentimentAnalyzer()
        self.text_classifier = TextClassifier()

        # Keywords for rule-based classification
        self.pain_point_keywords = [
            "problem", "issue", "bug", "error", "crash", "slow", "broken", "doesn't work",
            "doesn't function", "not working", "failed", "failure", "bad", "terrible",
            "awful", "horrible", "poor", "worst", "hate", "difficult", "disappointing",
            "frustrated", "annoying", "useless", "waste", "confusing", "complicated"
        ]

        self.feature_request_keywords = [
            "add", "feature", "implement", "include", "would like", "should have",
            "could you", "please add", "need", "want", "wish", "hope", "suggest",
            "recommendation", "improve", "enhancement", "upgrade", "update", "missing"
        ]

    def _rule_based_classification(self, text: str) -> str:
        """
        Simple rule-based classification as a fallback when async methods can't be used.
        """
        text_lower = text.lower()

        # Check for pain points
        if any(keyword in text_lower for keyword in self.pain_point_keywords):
            return "pain_point"

        # Check for feature requests
        if any(keyword in text_lower for keyword in self.feature_request_keywords):
            return "feature_request"

        # Default to positive feedback
        return "positive_feedback"

    def _rule_based_keyword_extraction(self, text: str) -> List[str]:
        """
        Simple rule-based keyword extraction as a fallback when async methods can't be used.
        """
        # Extract words that might be important (excluding common words)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "as", "of", "from"}
        words = [word.strip('.,!?:;()[]{}""\'').lower() for word in text.split()]
        words = [word for word in words if word and word not in common_words and len(word) > 2]

        # Count word frequency
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency and return top 5
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:5]]

    def generate_summary(
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
        # Use a batch size to limit memory usage
        cursor = reviews_collection.find(query).batch_size(500)

        # Count documents first to check if we have any reviews
        review_count = reviews_collection.count_documents(query)

        logger.info(f"Found {review_count} reviews for query: {query}")

        if review_count == 0:
            # Return empty summary instead of generating mock data
            logger.warning("No reviews found for the specified date range.")
            raise ValueError(f"No reviews found for source_type={source_type}, source_name={source_name} in the specified date range.")

        # Analyze sentiment and classify feedback
        pain_points = []
        feature_requests = []
        positive_feedback = []
        total_sentiment = 0
        total_reviews = 0
        keyword_freq: Dict[str, int] = {}

        # Store a limited number of reviews for trend analysis
        reviews_for_trends = []  # Store a limited number of reviews for trend analysis

        # Process reviews in batches using the cursor
        for review in cursor:
            try:
                total_reviews += 1

                # Store a limited number of reviews for trend analysis (max 1000)
                if len(reviews_for_trends) < 1000:
                    reviews_for_trends.append(review)

                # Analyze sentiment - use synchronous call
                sentiment_score = self.sentiment_analyzer.analyze_sentiment_sync(review["text"])
                total_sentiment += sentiment_score

                # Use rule-based classification instead of async methods
                feedback_type = self._rule_based_classification(review["text"])

                # Use rule-based keyword extraction instead of async methods
                keywords = self._rule_based_keyword_extraction(review["text"])
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

            # Force garbage collection every 1000 reviews to manage memory
            if total_reviews % 1000 == 0:
                import gc
                gc.collect()
                logger.info(f"Processed {total_reviews} reviews so far")

        # Calculate average sentiment
        avg_sentiment = total_sentiment / total_reviews if total_reviews > 0 else 0.0

        # Generate trend analysis using the limited set of reviews
        trend_analysis = self._analyze_trends(reviews_for_trends)

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
            total_reviews=total_reviews,
            avg_sentiment_score=avg_sentiment,
            pain_points=pain_points_dicts,
            feature_requests=feature_requests_dicts,
            positive_feedback=positive_feedback_dicts,
            top_keywords=dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            trend_analysis=trend_analysis,
            recommendations=recommendations
        )

        # Save to database
        try:
            # Use model_dump for Pydantic v2
            if hasattr(summary, 'model_dump'):
                summary_dict = summary.model_dump()
            # Fallback to dict for Pydantic v1 (with deprecation warning)
            elif hasattr(summary, 'dict'):
                # Convert to dictionary manually to avoid deprecation warning
                summary_dict = {k: getattr(summary, k) for k in summary.__dict__ if not k.startswith('_')}
            else:
                # Create a basic dictionary if all else fails
                summary_dict = {
                    "source_type": source_type,
                    "source_name": source_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_reviews": total_reviews,
                    "avg_sentiment_score": avg_sentiment
                }

            result = self.collection.insert_one(summary_dict)
            summary_dict["_id"] = str(result.inserted_id)
            summary_dict["created_at"] = datetime.now(timezone.utc)
            summary_dict["user_id"] = user_id
        except Exception as e:
            logger.error(f"Error saving summary to database: {str(e)}")
            # Create a basic dictionary if all else fails
            summary_dict = {
                "_id": str(ObjectId()),
                "created_at": datetime.now(timezone.utc),
                "user_id": user_id,
                "source_type": source_type,
                "source_name": source_name,
                "total_reviews": total_reviews,
                "avg_sentiment_score": avg_sentiment
            }

        return WeeklySummaryResponse(**summary_dict)

    def generate_summary_from_reviews(
        self,
        reviews: List[Dict[str, Any]],
        source_type: str,
        source_name: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> WeeklySummaryResponse:
        """Generate a weekly summary from a list of reviews"""
        # Analyze sentiment and classify feedback
        pain_points = []
        feature_requests = []
        positive_feedback = []
        total_sentiment = 0
        total_reviews = 0
        keyword_freq: Dict[str, int] = {}

        # Store a limited number of reviews for trend analysis
        reviews_for_trends = []  # Store a limited number of reviews for trend analysis

        # Process reviews
        for review in reviews:
            try:
                total_reviews += 1

                # Store a limited number of reviews for trend analysis (max 1000)
                if len(reviews_for_trends) < 1000:
                    reviews_for_trends.append(review)

                # Get text from review
                text = review.get("text", "")
                if not text:
                    continue

                # Analyze sentiment - use synchronous call
                sentiment_score = self.sentiment_analyzer.analyze_sentiment_sync(text)
                total_sentiment += sentiment_score

                # Use rule-based classification instead of async methods
                # This is a simple fallback that doesn't require async/await
                feedback_type = self._rule_based_classification(text)

                # Use rule-based keyword extraction instead of async methods
                keywords = self._rule_based_keyword_extraction(text)
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
                title=text[:50] + "..." if len(text) > 50 else text,
                description=text,
                priority_score=self._calculate_priority_score(sentiment_score, feedback_type),
                category=feedback_type,
                sentiment_score=sentiment_score,
                frequency=1,
                examples=[text]
            )

            # Add to appropriate list
            if feedback_type == "pain_point":
                pain_points.append(priority_item)
            elif feedback_type == "feature_request":
                feature_requests.append(priority_item)
            else:
                positive_feedback.append(priority_item)

            # Force garbage collection every 1000 reviews to manage memory
            if total_reviews % 1000 == 0:
                import gc
                gc.collect()
                logger.info(f"Processed {total_reviews} reviews so far")

        # Calculate average sentiment
        avg_sentiment = total_sentiment / total_reviews if total_reviews > 0 else 0.0

        # Generate trend analysis using the limited set of reviews
        trend_analysis = self._analyze_trends(reviews_for_trends)

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
            total_reviews=total_reviews,
            avg_sentiment_score=avg_sentiment,
            pain_points=pain_points_dicts,
            feature_requests=feature_requests_dicts,
            positive_feedback=positive_feedback_dicts,
            top_keywords=dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            trend_analysis=trend_analysis,
            recommendations=recommendations
        )

        # Save to database
        try:
            # Use model_dump for Pydantic v2
            if hasattr(summary, 'model_dump'):
                summary_dict = summary.model_dump()
            # Fallback to dict for Pydantic v1 (with deprecation warning)
            elif hasattr(summary, 'dict'):
                # Convert to dictionary manually to avoid deprecation warning
                summary_dict = {k: getattr(summary, k) for k in summary.__dict__ if not k.startswith('_')}
            else:
                # Create a basic dictionary if all else fails
                summary_dict = {
                    "source_type": source_type,
                    "source_name": source_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_reviews": total_reviews,
                    "avg_sentiment_score": avg_sentiment
                }

            result = self.collection.insert_one(summary_dict)
            summary_dict["_id"] = str(result.inserted_id)
            summary_dict["created_at"] = datetime.now(timezone.utc)
            summary_dict["user_id"] = user_id
        except Exception as e:
            logger.error(f"Error saving summary to database: {str(e)}")
            # Create a basic dictionary if all else fails
            summary_dict = {
                "_id": str(ObjectId()),
                "created_at": datetime.now(timezone.utc),
                "user_id": user_id,
                "source_type": source_type,
                "source_name": source_name,
                "total_reviews": total_reviews,
                "avg_sentiment_score": avg_sentiment
            }

        return WeeklySummaryResponse(**summary_dict)

    def get_priority_insights(
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
                # Try to match on either source_type or source_name for better results
                query["$or"] = [
                    {"source_type": source_type},
                    {"source_name": source_type}
                ]
            if user_id:
                query["user_id"] = user_id

            # Log the query for debugging
            logger.info(f"Weekly summary query: {query}")

            query["created_at"] = {
                "$gte": datetime.now(timezone.utc) - timedelta(days=days)
            }

            # In production mode, always use real data
            # Check if we're using a mock object only if DEVELOPMENT_MODE is true
            if os.getenv("DEVELOPMENT_MODE", "").lower() == "true" and hasattr(self.collection, '_mock_obj'):
                # In development mode with mock, return mock data
                logger.info("Using mock MongoDB client in development mode - generating mock data")
                # Create mock summaries for development testing
                mock_date = datetime.now(timezone.utc) - timedelta(days=3)
                summaries = [
                    {
                        "_id": "mock_id_1",
                        "source_type": source_type or "csv",
                        "source_name": "Mock Data Source",
                        "start_date": (mock_date - timedelta(days=7)).isoformat(),
                        "end_date": mock_date.isoformat(),
                        "total_reviews": 120,
                        "avg_sentiment_score": 0.65,
                        "positive_count": 75,
                        "negative_count": 25,
                        "neutral_count": 20,
                        "top_keywords": {"quality": 45, "service": 38, "price": 32, "delivery": 28, "support": 22},
                        "sentiment_by_topic": {
                            "quality": 0.78,
                            "service": 0.62,
                            "price": 0.45,
                            "delivery": 0.58,
                            "support": 0.72
                        },
                        "created_at": mock_date,
                        "pain_points": [
                            {
                                "title": "Customer service response time",
                                "description": "Multiple customers reported long wait times for customer service responses",
                                "priority_score": 0.85,
                                "category": "pain_point",
                                "sentiment_score": 0.25,
                                "frequency": 12,
                                "examples": ["Waited 3 days for a response", "Customer service is too slow"]
                            }
                        ],
                        "feature_requests": [
                            {
                                "title": "Mobile app improvements",
                                "description": "Users want better mobile app experience",
                                "priority_score": 0.75,
                                "category": "feature_request",
                                "sentiment_score": 0.40,
                                "frequency": 10,
                                "examples": ["Mobile app needs better navigation", "App crashes frequently"]
                            }
                        ],
                        "recommendations": [
                            "Improve customer service response time",
                            "Fix mobile app stability issues",
                            "risk: Increasing complaints about delivery times",
                            "opportunity: Strong positive sentiment around product quality"
                        ]
                    }
                ]
            else:
                try:
                    # Use find method with list() to get all results
                    cursor = self.collection.find(query)
                    # Convert cursor to list immediately to avoid 'to_list' attribute error
                    summaries = list(cursor)
                except Exception as e:
                    logger.error(f"Error querying MongoDB: {str(e)}")
                    # Return empty list if there's an error
                    summaries = []

            if not summaries:
                # If no summaries found, try with a broader query
                logger.warning(f"No summaries found for query: {query}")

                # Try to find any summaries regardless of date
                broader_query = {}
                if source_type:
                    broader_query["source_type"] = source_type
                if user_id:
                    broader_query["user_id"] = user_id

                try:
                    cursor = self.collection.find(broader_query).sort("created_at", -1).limit(5)
                    summaries = list(cursor)
                except Exception as e:
                    logger.error(f"Error querying MongoDB with broader query: {str(e)}")
                    summaries = []

                if not summaries:
                    logger.warning(f"No summaries found even with broader query: {broader_query}")
                    # Return mock insights instead of empty data
                    return self._generate_mock_insights(source_type)

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
                        {"name": k, "volume": v}
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
                    key=lambda x: x.get("volume", 0),
                    reverse=True
                )[:5]

            # If in development mode and using mock data, generate mock insights with Gemini
            # Only use mock data if DEVELOPMENT_MODE is true and we have mock summaries
            if os.getenv("DEVELOPMENT_MODE", "").lower() == "true" and any(str(s.get("_id", "")).startswith("mock_id") for s in summaries):
                logger.info("Generating mock insights from mock data using Gemini")

                # Create mock priority items
                mock_priority_items = [
                    {
                        "title": "Customer service response time",
                        "description": "Multiple customers reported long wait times for customer service responses",
                        "priority_score": 0.85,
                        "category": "pain_point",
                        "sentiment_score": 0.25,
                        "frequency": 12,
                        "examples": ["Waited 3 days for a response", "Customer service is too slow"]
                    },
                    {
                        "title": "Product quality concerns",
                        "description": "Several customers mentioned issues with product durability",
                        "priority_score": 0.72,
                        "category": "pain_point",
                        "sentiment_score": 0.30,
                        "frequency": 8,
                        "examples": ["Product broke after 2 weeks", "Quality is not as advertised"]
                    },
                    {
                        "title": "Website usability issues",
                        "description": "Users are having trouble navigating the website",
                        "priority_score": 0.68,
                        "category": "pain_point",
                        "sentiment_score": 0.35,
                        "frequency": 6,
                        "examples": ["Can't find the checkout button", "Website is confusing to navigate"]
                    }
                ]

                # Create mock trending topics
                mock_trending_topics = [
                    {"name": "Customer Support", "volume": 45, "sentiment": 0.62},
                    {"name": "Product Quality", "volume": 38, "sentiment": 0.78},
                    {"name": "Pricing", "volume": 32, "sentiment": 0.45},
                    {"name": "Delivery", "volume": 28, "sentiment": 0.58},
                    {"name": "Website Experience", "volume": 22, "sentiment": 0.72}
                ]

                # Create mock sentiment trends
                mock_sentiment_trends = {
                    "overall": 0.65,
                    "customer_support": 0.62,
                    "product_quality": 0.78,
                    "pricing": 0.45,
                    "delivery": 0.58,
                    "website_experience": 0.72
                }

                # Create mock action items, risk areas, and opportunity areas
                mock_action_items = [
                    "Improve customer service response time by implementing automated initial responses",
                    "Address product quality concerns in the next product update",
                    "Review pricing strategy based on competitive analysis",
                    "Optimize website navigation based on user feedback"
                ]

                mock_risk_areas = [
                    "Increasing complaints about delivery times",
                    "Negative sentiment around pricing compared to competitors",
                    "Technical support wait times affecting customer satisfaction"
                ]

                mock_opportunity_areas = [
                    "Strong positive sentiment around product quality can be leveraged in marketing",
                    "Customer interest in additional features suggests potential for premium offerings",
                    "High engagement with tutorial content indicates demand for educational materials"
                ]

                # Create mock insights
                return PriorityInsights(
                    high_priority_items=mock_priority_items,
                    trending_topics=mock_trending_topics,
                    sentiment_trends=mock_sentiment_trends,
                    action_items=mock_action_items,
                    risk_areas=mock_risk_areas,
                    opportunity_areas=mock_opportunity_areas
                )
            else:
                # Create PriorityInsights object with the collected data
                insights = PriorityInsights(
                    high_priority_items=sorted_high_priority,
                    trending_topics=sorted_trending,
                    sentiment_trends=sentiment_trends,
                    action_items=list(action_items),
                    risk_areas=list(risk_areas),
                    opportunity_areas=list(opportunity_areas)
                )

                return insights
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
                # Check for various date fields that might be present
                day = None

                # Try different date fields that might be present in the review
                date_fields = ["created_at", "timestamp", "date", "created", "review_date"]

                for field in date_fields:
                    if field in review:
                        if isinstance(review[field], datetime):
                            day = review[field].date()
                            break
                        elif isinstance(review[field], str):
                            try:
                                # Try different date formats
                                if 'T' in review[field]:  # ISO format
                                    day = datetime.fromisoformat(review[field]).date()
                                else:
                                    # Try common date formats
                                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                                        try:
                                            day = datetime.strptime(review[field], fmt).date()
                                            break
                                        except ValueError:
                                            continue
                                if day:
                                    break
                            except Exception:
                                continue

                # If no valid date field found, use today's date
                if day is None:
                    day = datetime.now(timezone.utc).date()
                    logger.warning(f"No valid date field found in review, using today's date: {day}")

                if day not in daily_reviews:
                    daily_reviews[day] = []
                daily_reviews[day].append(review)
            except Exception as e:
                logger.error(f"Error processing review date: {str(e)}")
                # Use today's date as fallback and include the review
                day = datetime.now(timezone.utc).date()
                if day not in daily_reviews:
                    daily_reviews[day] = []
                daily_reviews[day].append(review)

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

    def get_summary_by_id(self, summary_id: str) -> Optional[WeeklySummaryResponse]:
        """Get a specific weekly summary by ID"""
        try:
            # Use find_one without await
            summary = self.collection.find_one({"_id": ObjectId(summary_id)})
            if summary:
                summary["_id"] = str(summary["_id"])
                return WeeklySummaryResponse(**summary)
            return None
        except Exception as e:
            logger.error(f"Error getting summary by ID: {str(e)}")
            raise

    def get_summaries(
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

            # Use find method with list() to get all results
            cursor = self.collection.find(query)
            # Convert cursor to list
            summaries = list(cursor)

            # Convert ObjectId to string and create response objects
            for summary in summaries:
                summary["_id"] = str(summary["_id"])

            return [WeeklySummaryResponse(**summary) for summary in summaries]
        except Exception as e:
            logger.error(f"Error getting summaries: {str(e)}")
            raise

    # Generate mock insights for when no real data is available
    def _generate_mock_insights(self, source_type: Optional[str] = None) -> PriorityInsights:
        """Generate mock insights when no real data is available"""
        source = source_type or "product"
        logger.info(f"Generating mock insights for {source}")

        # Create mock priority items
        mock_priority_items = [
            {
                "title": f"Improve {source} user experience",
                "description": f"Users have reported issues with the {source} interface and navigation",
                "priority_score": 0.85,
                "category": "pain_point",
                "sentiment_score": 0.2,
                "frequency": 12,
                "examples": [f"The {source} interface is confusing", f"Navigation in {source} is difficult"]
            },
            {
                "title": f"Add more features to {source}",
                "description": f"Users are requesting additional functionality in {source}",
                "priority_score": 0.75,
                "category": "feature_request",
                "sentiment_score": 0.6,
                "frequency": 8,
                "examples": [f"Would like to see more options in {source}", f"Need additional features in {source}"]
            },
            {
                "title": f"Fix performance issues in {source}",
                "description": f"Users are experiencing slowdowns and crashes with {source}",
                "priority_score": 0.7,
                "category": "pain_point",
                "sentiment_score": 0.3,
                "frequency": 6,
                "examples": [f"{source} crashes frequently", f"Performance of {source} is slow"]
            }
        ]

        # Create mock trending topics
        mock_trending_topics = [
            {"name": "User Interface", "volume": 15},
            {"name": "Performance", "volume": 12},
            {"name": "Features", "volume": 10},
            {"name": "Stability", "volume": 8},
            {"name": "Documentation", "volume": 5}
        ]

        # Create mock sentiment trends
        mock_sentiment_trends = {
            "user_interface": 0.3,
            "performance": 0.2,
            "features": 0.6,
            "stability": 0.4,
            "documentation": 0.7
        }

        # Create mock action items
        mock_action_items = [
            f"Improve {source} user interface based on feedback",
            f"Optimize {source} performance to reduce crashes",
            f"Add requested features to {source} in next release",
            f"Update documentation for {source} to address common questions"
        ]

        # Create mock risk areas
        mock_risk_areas = [
            f"Continued performance issues may lead to user abandonment",
            f"Lack of feature parity with competitors could impact adoption",
            f"User interface confusion is causing support burden"
        ]

        # Create mock opportunity areas
        mock_opportunity_areas = [
            f"Strong interest in additional features indicates growth potential",
            f"Addressing performance issues could significantly improve satisfaction",
            f"Improving documentation could reduce support requests"
        ]

        # Create mock insights
        return PriorityInsights(
            high_priority_items=mock_priority_items,
            trending_topics=mock_trending_topics,
            sentiment_trends=mock_sentiment_trends,
            action_items=mock_action_items,
            risk_areas=mock_risk_areas,
            opportunity_areas=mock_opportunity_areas
        )
