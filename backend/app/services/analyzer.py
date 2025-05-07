import re
import random
from typing import List, Dict, Any, Optional
import logging
import torch
import nltk
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os
import time

# Try to import Gemini service
try:
    from ..services.gemini_service import GeminiService
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class TextAnalyzer:
    def __init__(self, use_gemini: bool = True):
        # Keywords for classification
        self.pain_point_keywords = {'crash', 'error', 'bug', 'issue', 'problem', 'fail', 'slow', 'broken', 'bad', 'terrible', 'awful', 'horrible'}
        self.feature_request_keywords = {'add', 'implement', 'feature', 'request', 'suggest', 'need', 'want', 'would like', 'could use', 'should have'}

        # Initialize NLTK components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

        # Initialize Gemini service if available
        self.gemini_service = None
        self.use_gemini = use_gemini

        if GEMINI_AVAILABLE and use_gemini:
            try:
                self.gemini_service = GeminiService()
                if self.gemini_service.available:
                    logger.info("Gemini service initialized successfully")
                else:
                    logger.warning("Gemini service is not available, falling back to local models")
            except Exception as e:
                logger.error(f"Error initializing Gemini service: {str(e)}")
                logger.warning("Falling back to local models")

        # Load sentiment analysis model
        logger.info("Loading sentiment analysis model...")
        try:
            # Use a pre-trained sentiment analysis model from Hugging Face
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True
            )
            logger.info("Sentiment analysis model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment model: {str(e)}")
            # Fallback to simple sentiment analysis if model loading fails
            self.sentiment_model = None
            logger.warning("Using fallback sentiment analysis")

    def clean_text(self, text: str) -> str:
        # Convert to lowercase
        text = text.lower()

        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def extract_keywords(self, text: str, n_keywords: int = 5) -> List[str]:
        """
        Extract keywords from text using NLTK for tokenization, stopword removal, and lemmatization.

        Args:
            text: The text to extract keywords from
            n_keywords: Maximum number of keywords to return

        Returns:
            List of keywords
        """
        # Tokenize the text
        tokens = word_tokenize(text.lower())

        # Remove stopwords and short words
        filtered_tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2 and word.isalpha()]

        # Lemmatize words
        lemmatized_tokens = [self.lemmatizer.lemmatize(word) for word in filtered_tokens]

        # Count word frequency
        word_counts = {}
        for word in lemmatized_tokens:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Return top n keywords
        return [word for word, _ in sorted_words[:n_keywords]]

    def classify_feedback(self, text: str) -> str:
        text_lower = text.lower()

        # Check for pain points
        if any(keyword in text_lower for keyword in self.pain_point_keywords):
            return "pain_point"

        # Check for feature requests
        if any(keyword in text_lower for keyword in self.feature_request_keywords):
            return "feature_request"

        # Default to positive feedback
        return "positive_feedback"

    def analyze_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Analyze text using advanced NLP techniques.

        Args:
            text: The text to analyze
            metadata: Optional metadata containing additional information

        Returns:
            Dictionary with sentiment score, sentiment label, category, and keywords
        """
        # Clean the text
        cleaned_text = self.clean_text(text)

        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}

        # Check if Gemini API is available and not rate limited or circuit breaker is open
        use_gemini = (self.gemini_service and
                     self.gemini_service.available and
                     self.use_gemini and
                     text.strip() and
                     not self.gemini_service._check_circuit_breaker() and  # Check circuit breaker
                     not (self.gemini_service.rate_limited and time.time() < self.gemini_service.rate_limit_reset_time))  # Check rate limit

        # Try Gemini API first if available and not rate limited/circuit open
        if use_gemini:
            try:
                start_time = time.time()
                logger.info("Using Gemini API for sentiment analysis")

                # Get sentiment from Gemini
                gemini_result = self.gemini_service.analyze_sentiment(text)

                sentiment_score = gemini_result.get("score", 0.5)
                sentiment_label = gemini_result.get("label", "NEUTRAL")
                confidence = gemini_result.get("confidence", 0.0)

                processing_time = time.time() - start_time
                logger.info(f"Gemini sentiment analysis completed in {processing_time:.2f} seconds")

            except Exception as e:
                logger.error(f"Error in Gemini sentiment analysis: {str(e)}")
                logger.warning("Falling back to local sentiment analysis")
                # Fall back to local sentiment analysis
                if self.sentiment_model:
                    sentiment_score, sentiment_label = self._transformer_sentiment_analysis(text)
                else:
                    sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)
        # Log why we're not using Gemini
        elif self.gemini_service and self.gemini_service._check_circuit_breaker():
            logger.info("Circuit breaker is open. Using local sentiment analysis")
            if self.sentiment_model:
                sentiment_score, sentiment_label = self._transformer_sentiment_analysis(text)
            else:
                sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)
        elif self.gemini_service and self.gemini_service.rate_limited:
            logger.info("Rate limited. Using local sentiment analysis")
            if self.sentiment_model:
                sentiment_score, sentiment_label = self._transformer_sentiment_analysis(text)
            else:
                sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)

        # Use transformer model if Gemini is not available
        elif self.sentiment_model and text.strip():
            sentiment_score, sentiment_label = self._transformer_sentiment_analysis(text)

        # Fall back to simple sentiment analysis
        else:
            sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)

        # Extract keywords
        keywords = self.extract_keywords(cleaned_text)

        # Use predefined category from metadata if available, otherwise classify
        if metadata and 'predefined_category' in metadata:
            category = metadata['predefined_category']
            logger.info(f"Using predefined category from metadata: {category}")
        else:
            category = self.classify_feedback(cleaned_text)

        result = {
            "sentiment_score": float(sentiment_score),  # Ensure it's a Python float
            "sentiment_label": sentiment_label,
            "category": category,
            "keywords": keywords
        }

        # Add metadata to result if provided
        if metadata:
            result["metadata"] = metadata

        return result

    def _transformer_sentiment_analysis(self, text: str) -> tuple:
        """
        Perform sentiment analysis using transformer model.

        Args:
            text: The text to analyze

        Returns:
            Tuple of (sentiment_score, sentiment_label)
        """
        try:
            # Get sentiment from model
            sentiment_results = self.sentiment_model(text[:512])  # Limit text length for model

            # Extract scores for POSITIVE and NEGATIVE labels
            scores = {item['label']: item['score'] for item in sentiment_results[0]}

            if 'POSITIVE' in scores:
                sentiment_score = scores['POSITIVE']
                sentiment_label = "POSITIVE" if sentiment_score > 0.5 else "NEGATIVE"
            else:
                # Handle different label formats
                positive_score = next((item['score'] for item in sentiment_results[0] if item['label'].lower() in ['positive', 'pos']), 0.5)
                sentiment_score = positive_score
                sentiment_label = "POSITIVE" if sentiment_score > 0.5 else "NEGATIVE"

            # Adjust score to be between 0 and 1
            if sentiment_label == "NEGATIVE":
                sentiment_score = 1 - sentiment_score

            # Set NEUTRAL for borderline cases
            if 0.4 <= sentiment_score <= 0.6:
                sentiment_label = "NEUTRAL"

            return sentiment_score, sentiment_label

        except Exception as e:
            logger.error(f"Error in transformer sentiment analysis: {str(e)}")
            # Fall back to simple sentiment analysis
            return self._simple_sentiment_analysis(self.clean_text(text))

    def _simple_sentiment_analysis(self, text: str) -> tuple:
        """
        Perform simple rule-based sentiment analysis as a fallback.

        Args:
            text: The cleaned text to analyze

        Returns:
            Tuple of (sentiment_score, sentiment_label)
        """
        # Count positive and negative words
        positive_words = {'good', 'great', 'excellent', 'awesome', 'amazing', 'love', 'like',
                         'best', 'perfect', 'nice', 'helpful', 'recommend', 'easy', 'fantastic',
                         'wonderful', 'happy', 'pleased', 'satisfied', 'enjoy', 'impressive'}

        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'worst',
                         'poor', 'disappointing', 'difficult', 'hard', 'confusing', 'slow',
                         'expensive', 'useless', 'annoying', 'frustrating', 'problem', 'issue', 'bug'}

        words = text.split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        # Calculate sentiment score
        if positive_count > negative_count:
            sentiment_score = 0.5 + (positive_count - negative_count) / (positive_count + negative_count + 1) * 0.5
            sentiment_label = "POSITIVE"
        elif negative_count > positive_count:
            sentiment_score = 0.5 - (negative_count - positive_count) / (positive_count + negative_count + 1) * 0.5
            sentiment_label = "NEGATIVE"
        else:
            sentiment_score = 0.5
            sentiment_label = "NEUTRAL"

        return sentiment_score, sentiment_label

    def analyze_texts_batch(self, texts: List[str], metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[Dict]:
        """
        Analyze multiple texts in batch for more efficient processing.

        Args:
            texts: List of texts to analyze
            metadata_list: Optional list of metadata dictionaries, one per text

        Returns:
            List of analysis results
        """
        # Initialize metadata list if not provided
        if metadata_list is None:
            metadata_list = [None] * len(texts)
        results = []

        # Check if Gemini API is available
        gemini_available = (self.gemini_service and
                           self.gemini_service.available and
                           self.use_gemini and
                           texts)

        # Only check circuit breaker and rate limit if Gemini is available
        if gemini_available:
            circuit_open = self.gemini_service._check_circuit_breaker()
            rate_limited = self.gemini_service.rate_limited and time.time() < self.gemini_service.rate_limit_reset_time
            use_gemini = not circuit_open and not rate_limited
        else:
            use_gemini = False
            circuit_open = False
            rate_limited = False

        if use_gemini:
            try:
                start_time = time.time()
                logger.info(f"Using Gemini API for batch sentiment analysis of {len(texts)} texts")

                # Create a callback function to log batch progress and update WebSocket
                def batch_progress_callback(current_batch, total_batches, batch_time, items_processed, avg_speed, estimated_time_remaining):
                    # Log progress
                    logger.info(f"Batch progress: {current_batch}/{total_batches} " +
                               f"({items_processed}/{len(texts)} items, " +
                               f"{avg_speed:.2f} items/sec, " +
                               f"~{estimated_time_remaining:.1f}s remaining)")

                    # Get user ID from metadata if available
                    user_id = None
                    if metadata_list and len(metadata_list) > 0 and metadata_list[0]:
                        user_id = metadata_list[0].get("user_id")

                    # If we have a user ID, send WebSocket update
                    if user_id:
                        from ..api.websocket_routes import batch_progress_callback as ws_callback
                        ws_callback(
                            user_id=user_id,
                            current_batch=current_batch,
                            total_batches=total_batches,
                            batch_time=batch_time,
                            items_processed=items_processed,
                            total_items=len(texts),
                            avg_speed=avg_speed,
                            estimated_time_remaining=estimated_time_remaining
                        )

                # Get sentiment from Gemini in batch with progress reporting
                gemini_results = self.gemini_service.analyze_reviews(texts, callback=batch_progress_callback)

                # Log completion
                logger.info(f"Batch sentiment analysis completed for all {len(texts)} reviews")

                processing_time = time.time() - start_time
                logger.info(f"Gemini batch sentiment analysis completed in {processing_time:.2f} seconds")

                # Process each result
                for i, (text, gemini_result) in enumerate(zip(texts, gemini_results)):
                    # Clean the text
                    cleaned_text = self.clean_text(text)

                    # Get metadata for this text
                    metadata = metadata_list[i] if i < len(metadata_list) else None

                    # Extract sentiment data
                    sentiment_score = gemini_result.get("score", 0.5)
                    sentiment_label = gemini_result.get("label", "NEUTRAL")

                    # Extract keywords (still done individually)
                    keywords = self.extract_keywords(cleaned_text)

                    # Use predefined category from metadata if available, otherwise classify
                    if metadata and 'predefined_category' in metadata:
                        category = metadata['predefined_category']
                        logger.info(f"Using predefined category from metadata: {category}")
                    else:
                        category = self.classify_feedback(cleaned_text)

                    # Create result dictionary
                    result = {
                        "sentiment_score": float(sentiment_score),
                        "sentiment_label": sentiment_label,
                        "category": category,
                        "keywords": keywords
                    }

                    # Add metadata to result if provided
                    if metadata:
                        result["metadata"] = metadata

                    # Add to results
                    results.append(result)

                return results

            except Exception as e:
                logger.error(f"Error in Gemini batch sentiment analysis: {str(e)}")
                logger.warning("Falling back to individual analysis")
                # Fall back to individual analysis
        else:
            # Log why we're not using Gemini
            if not gemini_available:
                if not self.gemini_service:
                    logger.info(f"Gemini service not configured. Using local processing for batch analysis of {len(texts)} texts")
                elif not self.gemini_service.available:
                    logger.info(f"Gemini API not available. Using local processing for batch analysis of {len(texts)} texts")
                elif not self.use_gemini:
                    logger.info(f"Gemini API disabled. Using local processing for batch analysis of {len(texts)} texts")
                elif not texts:
                    logger.info("No texts to analyze. Skipping Gemini API call.")
            elif circuit_open:
                logger.info(f"Circuit breaker is open. Using local processing for batch analysis of {len(texts)} texts")
            elif rate_limited:
                logger.info(f"Rate limited. Using local processing for batch analysis of {len(texts)} texts")

        # Process each text individually
        for i, text in enumerate(texts):
            metadata = metadata_list[i] if i < len(metadata_list) else None
            result = self.analyze_text(text, metadata)
            results.append(result)

        return results

    def generate_summary(self, reviews: List[Any]) -> Dict:
        """
        Generate a summary of the analyzed reviews.

        Args:
            reviews: List of analyzed review objects (either dictionaries or Pydantic models)

        Returns:
            Dictionary with pain points, feature requests, positive feedback, and suggested priorities
        """
        # Helper function to get attribute from either dict or object
        def get_attr(obj, attr):
            try:
                return obj[attr]  # Try dictionary access
            except (TypeError, KeyError):
                return getattr(obj, attr)  # Fall back to attribute access

        # Check if Gemini API is available
        gemini_available = (self.gemini_service and
                           self.gemini_service.available and
                           self.use_gemini and
                           reviews)

        # Only check circuit breaker and rate limit if Gemini is available
        if gemini_available:
            circuit_open = self.gemini_service._check_circuit_breaker()
            rate_limited = self.gemini_service.rate_limited and time.time() < self.gemini_service.rate_limit_reset_time
            use_gemini = not circuit_open and not rate_limited
        else:
            use_gemini = False
            circuit_open = False
            rate_limited = False

        # Try using Gemini for advanced insights if available and not rate limited/circuit open
        if use_gemini:
            try:
                start_time = time.time()
                logger.info("Using Gemini API for insights extraction")

                # Extract review texts
                review_texts = [get_attr(review, "text") for review in reviews if get_attr(review, "text")]

                if not review_texts:
                    logger.warning("No valid review texts found for Gemini insights extraction")
                    return self._traditional_summary(reviews)

                # Log the number of reviews being processed
                logger.info(f"Processing {len(review_texts)} reviews for insights extraction")

                # Get insights from Gemini (now with batching and rate limit handling)
                gemini_insights = self.gemini_service.extract_insights(review_texts)

            except Exception as e:
                logger.error(f"Error in Gemini insights extraction: {str(e)}")
                logger.warning("Falling back to traditional summary generation")
                # Add error information to the summary
                traditional_summary = self._traditional_summary(reviews)
                traditional_summary["error"] = str(e)
                traditional_summary["error_source"] = "gemini_api"
                return traditional_summary
        else:
            # Generate traditional summary
            traditional_summary = self._traditional_summary(reviews)

            # Log why we're not using Gemini and add note to summary
            if not gemini_available:
                if not self.gemini_service:
                    logger.info("Gemini service not configured. Using traditional summary generation")
                    traditional_summary["note"] = "Using local processing (Gemini not configured)"
                elif not self.gemini_service.available:
                    logger.info("Gemini API not available. Using traditional summary generation")
                    traditional_summary["note"] = "Using local processing (Gemini not available)"
                elif not self.use_gemini:
                    logger.info("Gemini API disabled. Using traditional summary generation")
                    traditional_summary["note"] = "Using local processing (Gemini disabled)"
                elif not reviews:
                    logger.info("No reviews to analyze. Using traditional summary generation")
                    traditional_summary["note"] = "Using local processing (no reviews to analyze)"
            elif circuit_open:
                logger.info("Circuit breaker is open. Using traditional summary generation")
                traditional_summary["note"] = "Using local processing due to circuit breaker"
            elif rate_limited:
                logger.info("Rate limited. Using traditional summary generation")
                traditional_summary["note"] = "Using local processing due to rate limiting"

            return traditional_summary

        # Process Gemini insights
        processing_time = time.time() - start_time
        logger.info(f"Gemini insights extraction completed in {processing_time:.2f} seconds")

        # Log the structure of the insights
        logger.info(f"Gemini insights keys: {list(gemini_insights.keys())}")
        logger.info(f"Pain points: {len(gemini_insights.get('pain_points', []))}, " +
                   f"Feature requests: {len(gemini_insights.get('feature_requests', []))}, " +
                   f"Positive aspects: {len(gemini_insights.get('positive_aspects', []))}")

        # Process the insights
        pain_points = []
        feature_requests = []
        positive_feedback = []
        priorities = []

        # Add pain points
        pain_points_list = gemini_insights.get("pain_points", [])
        if not pain_points_list:
            # Add a default pain point if none were found
            pain_points_list = ["No specific pain points identified in the reviews"]

        for i, point in enumerate(pain_points_list):
            # Skip empty strings
            if not point or not isinstance(point, str):
                continue

            pain_points.append({
                "text": point,
                "sentiment_score": 0.2,  # Low score for pain points
                "keywords": []
            })
            if i == 0 and "no specific" not in point.lower():
                priorities.append(f"Address critical issue: {point[:100]}...")

        # Add feature requests
        feature_requests_list = gemini_insights.get("feature_requests", [])
        if not feature_requests_list:
            # Add a default feature request if none were found
            feature_requests_list = ["No specific feature requests identified in the reviews"]

        for i, request in enumerate(feature_requests_list):
            # Skip empty strings
            if not request or not isinstance(request, str):
                continue

            feature_requests.append({
                "text": request,
                "sentiment_score": 0.7,  # Higher score for feature requests
                "keywords": []
            })
            if i == 0 and "no specific" not in request.lower():
                priorities.append(f"Implement requested feature: {request[:100]}...")

        # Add positive aspects
        positive_aspects_list = gemini_insights.get("positive_aspects", [])
        if not positive_aspects_list:
            # Add a default positive aspect if none were found
            positive_aspects_list = ["No specific positive aspects identified in the reviews"]

        for i, positive in enumerate(positive_aspects_list):
            # Skip empty strings
            if not positive or not isinstance(positive, str):
                continue

            positive_feedback.append({
                "text": positive,
                "sentiment_score": 0.9,  # High score for positive feedback
                "keywords": []
            })
            if i == 0 and "no specific" not in positive.lower():
                priorities.append(f"Maintain strengths: {positive[:100]}...")

        # If no priorities were added, add a general one from the summary
        if not priorities and "summary" in gemini_insights:
            priorities.append(f"General recommendation: {gemini_insights['summary'][:100]}...")

        # Ensure we have at least one item in each category
        if not pain_points:
            pain_points = [{
                "text": "No specific pain points identified in the reviews",
                "sentiment_score": 0.5,
                "keywords": []
            }]

        if not feature_requests:
            feature_requests = [{
                "text": "No specific feature requests identified in the reviews",
                "sentiment_score": 0.5,
                "keywords": []
            }]

        if not positive_feedback:
            positive_feedback = [{
                "text": "No specific positive feedback identified in the reviews",
                "sentiment_score": 0.5,
                "keywords": []
            }]

        if not priorities:
            priorities = ["No specific priorities identified based on the reviews"]

        # Log the final counts
        logger.info(f"Final summary counts - Pain points: {len(pain_points)}, " +
                   f"Feature requests: {len(feature_requests)}, " +
                   f"Positive feedback: {len(positive_feedback)}, " +
                   f"Priorities: {len(priorities)}")

        return {
            "pain_points": pain_points[:3],
            "feature_requests": feature_requests[:3],
            "positive_feedback": positive_feedback[:3],
            "suggested_priorities": priorities,
            "gemini_powered": True,
            "processing_time": processing_time
        }

    def _traditional_summary(self, reviews: List[Any]) -> Dict:
        """
        Generate a summary using traditional methods.

        Args:
            reviews: List of analyzed review objects

        Returns:
            Dictionary with summary information
        """
        # Helper function to get attribute from either dict or object
        def get_attr(obj, attr):
            try:
                return obj[attr]  # Try dictionary access
            except (TypeError, KeyError):
                return getattr(obj, attr)  # Fall back to attribute access

        # Group reviews by category
        pain_points = []
        feature_requests = []
        positive_feedback = []

        for review in reviews:
            # Handle both dictionary and Pydantic model access
            try:
                # Try dictionary-style access first
                category = review["category"]
            except (TypeError, KeyError):
                # Fall back to attribute access for Pydantic models
                category = review.category

            if category == "pain_point":
                pain_points.append(review)
            elif category == "feature_request":
                feature_requests.append(review)
            else:
                positive_feedback.append(review)

        # Sort by sentiment score (ascending for pain points, descending for others)
        pain_points.sort(key=lambda x: get_attr(x, "sentiment_score"))
        feature_requests.sort(key=lambda x: get_attr(x, "sentiment_score"), reverse=True)
        positive_feedback.sort(key=lambda x: get_attr(x, "sentiment_score"), reverse=True)

        # Generate suggested priorities
        priorities = []

        # Add pain points to priorities (most critical first)
        if pain_points:
            text = get_attr(pain_points[0], "text")
            priorities.append(f"Address critical issue: {text[:100]}...")

            # Add more pain points if available
            if len(pain_points) > 1:
                text = get_attr(pain_points[1], "text")
                priorities.append(f"Fix secondary issue: {text[:100]}...")

        # Add feature requests to priorities
        if feature_requests:
            text = get_attr(feature_requests[0], "text")
            priorities.append(f"Implement requested feature: {text[:100]}...")

        # Add general recommendation
        if positive_feedback:
            text = get_attr(positive_feedback[0], "text")
            priorities.append(f"Maintain strengths: {text[:100]}...")

        # Get top 3 of each category (or fewer if not available)
        top_pain_points = pain_points[:3]
        top_feature_requests = feature_requests[:3]
        top_positive_feedback = positive_feedback[:3]

        # Create summary items with required fields
        pain_point_items = [
            {
                "text": get_attr(item, "text"),
                "sentiment_score": get_attr(item, "sentiment_score"),
                "keywords": get_attr(item, "keywords")
            } for item in top_pain_points
        ]

        feature_request_items = [
            {
                "text": get_attr(item, "text"),
                "sentiment_score": get_attr(item, "sentiment_score"),
                "keywords": get_attr(item, "keywords")
            } for item in top_feature_requests
        ]

        positive_feedback_items = [
            {
                "text": get_attr(item, "text"),
                "sentiment_score": get_attr(item, "sentiment_score"),
                "keywords": get_attr(item, "keywords")
            } for item in top_positive_feedback
        ]

        return {
            "pain_points": pain_point_items,
            "feature_requests": feature_request_items,
            "positive_feedback": positive_feedback_items,
            "suggested_priorities": priorities,
            "gemini_powered": False
        }