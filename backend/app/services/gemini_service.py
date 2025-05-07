"""
Gemini API service for faster data processing.
This service provides integration with Google's Gemini API for advanced text analysis.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI is not installed. Gemini functionality will be disabled.")
    GEMINI_AVAILABLE = False

class GeminiService:
    """
    Service for interacting with Google's Gemini API for text analysis.
    """

    def __init__(self):
        """
        Initialize the Gemini service with API key from environment variables.
        """
        logger.info("Initializing Gemini Service...")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.available = GEMINI_AVAILABLE and self.api_key is not None

        # Rate limit tracking
        self.rate_limited = False
        self.rate_limit_reset_time = 0
        self.consecutive_failures = 0
        self.max_retries = 3
        self.backoff_factor = 2
        self.initial_wait_time = 5  # seconds

        # Circuit breaker pattern
        self.circuit_open = False  # When True, circuit is "open" and we bypass Gemini API completely
        self.circuit_reset_time = 0  # When to try closing the circuit again
        self.failure_threshold = 3  # Number of consecutive failures before opening circuit
        self.circuit_reset_timeout = 2 * 60  # 2 minutes - how long to keep circuit open

        # Cache for API responses
        self.sentiment_cache = {}
        self.insight_cache = {}

        if not GEMINI_AVAILABLE:
            logger.warning("Gemini API not available: google-generativeai package not installed")
            return

        if not self.api_key:
            logger.warning("Gemini API not available: GEMINI_API_KEY not set in environment variables")
            return

        try:
            # Configure the Gemini API
            genai.configure(api_key=self.api_key)

            # Get available models
            try:
                self.models = [m.name for m in genai.list_models() if 'gemini' in m.name]

                if not self.models:
                    logger.warning("No Gemini models available")
                    self.available = False
                    return

                # Check if specified model is available
                if self.model_name not in self.models:
                    logger.warning(f"Specified model {self.model_name} not available. Using {self.models[0]} instead.")
                    self.model_name = self.models[0]
            except Exception as model_error:
                logger.warning(f"Could not list Gemini models: {str(model_error)}. Using default model: {self.model_name}")
                # Continue with the default model even if we can't list available models

            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini service initialized with model: {self.model_name}")

        except Exception as e:
            logger.error(f"Error initializing Gemini API: {str(e)}")
            self.available = False

    def _check_circuit_breaker(self) -> bool:
        """
        Check if the circuit breaker is open (True) or closed (False).
        If open, check if it's time to try closing it.

        Returns:
            True if circuit is open (bypass Gemini API), False if closed (use Gemini API)
        """
        # If circuit is open, check if it's time to try closing it
        if self.circuit_open:
            current_time = time.time()
            if current_time >= self.circuit_reset_time:
                logger.info("Circuit breaker reset time reached. Attempting to close circuit.")
                self.circuit_open = False
                self.consecutive_failures = 0
                return False
            else:
                # Circuit still open
                time_remaining = int(self.circuit_reset_time - current_time)
                logger.info(f"Circuit breaker open. Using local processing for {time_remaining} more seconds.")
                return True

        # Circuit is closed
        return False

    def _open_circuit(self):
        """
        Open the circuit breaker to bypass Gemini API calls for a period of time.
        """
        self.circuit_open = True
        self.circuit_reset_time = time.time() + self.circuit_reset_timeout
        logger.warning(f"Circuit breaker OPENED. Bypassing Gemini API for {self.circuit_reset_timeout} seconds.")

    def get_service_status(self) -> dict:
        """
        Get the current status of the Gemini service.

        Returns:
            Dictionary with service status information
        """
        current_time = time.time()

        status = {
            "available": self.available,
            "model": self.model_name,
            "rate_limited": self.rate_limited,
            "circuit_open": self.circuit_open,
            "using_local_processing": self.rate_limited or self.circuit_open or not self.available
        }

        # Add rate limit information if applicable
        if self.rate_limited and current_time < self.rate_limit_reset_time:
            status["rate_limit_reset_in"] = int(self.rate_limit_reset_time - current_time)

        # Add circuit breaker information if applicable
        if self.circuit_open:
            status["circuit_reset_in"] = int(self.circuit_reset_time - current_time)

        return status

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Gemini API.

        Args:
            text: The text to analyze

        Returns:
            Dictionary with sentiment analysis results
        """
        if not self.available:
            logger.warning("Gemini API not available for sentiment analysis")
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

        # Check cache first
        if text in self.sentiment_cache:
            return self.sentiment_cache[text]

        # Check if circuit breaker is open
        if self._check_circuit_breaker():
            logger.info("Circuit breaker open. Using fallback sentiment analysis.")
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback sentiment analysis due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

        try:
            start_time = time.time()

            prompt = f"""
            Analyze the sentiment of the following text and return a JSON object with:
            - score: a float between 0 (negative) and 1 (positive)
            - label: one of "POSITIVE", "NEGATIVE", or "NEUTRAL"
            - confidence: a float between 0 and 1 indicating confidence in the analysis

            Text: "{text}"

            Return only the JSON object without any additional text.
            """

            response = self.model.generate_content(prompt)

            # Extract JSON from response
            try:
                # Try to parse the response text as JSON
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from the text
                response_text = response.text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "", 1)
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]
                response_text = response_text.strip()
                result = json.loads(response_text)

            processing_time = time.time() - start_time
            logger.info(f"Gemini sentiment analysis completed in {processing_time:.2f} seconds")

            # Reset failure counter on success
            self.consecutive_failures = 0

            # Cache the result
            self.sentiment_cache[text] = result

            return result

        except Exception as e:
            logger.error(f"Error in Gemini sentiment analysis: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()
            else:
                # For non-rate-limit errors, still increment failure counter but with less weight
                self.consecutive_failures += 0.5

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

    def analyze_reviews(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple reviews in batch for faster processing.

        Args:
            reviews: List of review texts to analyze

        Returns:
            List of dictionaries with analysis results
        """
        if not self.available:
            logger.warning("Gemini API not available for review analysis")
            return [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in reviews]

        # Check if circuit breaker is open
        if self._check_circuit_breaker():
            logger.info("Circuit breaker open. Using fallback batch sentiment analysis.")
            return [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in reviews]

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback sentiment analysis due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            return [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in reviews]

        # Check cache first and collect uncached reviews
        results = []
        uncached_reviews = []
        uncached_indices = []

        for i, review in enumerate(reviews):
            if review in self.sentiment_cache:
                results.append(self.sentiment_cache[review])
            else:
                results.append(None)  # Placeholder
                uncached_reviews.append(review)
                uncached_indices.append(i)

        # If all reviews were cached, return results
        if not uncached_reviews:
            return results

        # Process reviews in smaller batches if there are too many
        if len(uncached_reviews) > 20:
            logger.info(f"Processing {len(uncached_reviews)} reviews in batches for sentiment analysis")

            # Split reviews into batches of 20
            batches = [uncached_reviews[i:i+20] for i in range(0, len(uncached_reviews), 20)]
            batch_indices = [uncached_indices[i:i+20] for i in range(0, len(uncached_indices), 20)]

            # Process each batch
            for i, (batch, indices) in enumerate(zip(batches, batch_indices)):
                logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} reviews")

                # Process this batch
                batch_results = self._analyze_reviews_single_batch(batch)

                # Update results and cache
                for j, result in enumerate(batch_results):
                    original_index = indices[j]
                    results[original_index] = result
                    self.sentiment_cache[batch[j]] = result

                # Add a small delay between batches to avoid rate limiting
                if i < len(batches) - 1:
                    time.sleep(1)

            return results
        else:
            # Process all uncached reviews in a single batch
            batch_results = self._analyze_reviews_single_batch(uncached_reviews)

            # Update results and cache
            for i, result in enumerate(batch_results):
                original_index = uncached_indices[i]
                results[original_index] = result
                self.sentiment_cache[uncached_reviews[i]] = result

            return results

    def _analyze_reviews_single_batch(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze a single batch of reviews.
        """
        try:
            start_time = time.time()

            # Prepare the prompt with all reviews
            reviews_text = "\n".join([f"Review {i+1}: {review}" for i, review in enumerate(reviews)])

            prompt = f"""
            Analyze the sentiment of each of the following reviews and return a JSON array of objects.
            Each object should have:
            - score: a float between 0 (negative) and 1 (positive)
            - label: one of "POSITIVE", "NEGATIVE", or "NEUTRAL"
            - confidence: a float between 0 and 1 indicating confidence in the analysis

            Reviews:
            {reviews_text}

            Return only the JSON array without any additional text.
            """

            response = self.model.generate_content(prompt)

            # Extract JSON from response
            try:
                # Try to parse the response text as JSON
                results = json.loads(response.text)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from the text
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1)
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()
                results = json.loads(text)

            processing_time = time.time() - start_time
            logger.info(f"Gemini batch review analysis completed in {processing_time:.2f} seconds for {len(reviews)} reviews")

            # Reset failure counter on success
            self.consecutive_failures = 0

            return results

        except Exception as e:
            logger.error(f"Error in Gemini batch review analysis: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded in batch analysis. Using fallback for {wait_time} seconds.")

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()
            else:
                # For non-rate-limit errors, still increment failure counter but with less weight
                self.consecutive_failures += 0.5

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

            return [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in reviews]

    def extract_insights(self, reviews: List[str]) -> Dict[str, Any]:
        """
        Extract insights from a collection of reviews.

        Args:
            reviews: List of review texts

        Returns:
            Dictionary with insights
        """
        if not self.available:
            logger.warning("Gemini API not available for insight extraction")
            return {
                "summary": "Insights not available - Gemini API not configured",
                "key_points": ["Local processing active - Gemini API not available"],
                "pain_points": ["Using local processing due to API unavailability"],
                "feature_requests": ["Consider configuring Gemini API for better insights"],
                "positive_aspects": ["Basic analysis still available without Gemini API"]
            }

        # Check if circuit breaker is open
        if self._check_circuit_breaker():
            logger.info("Circuit breaker open. Using fallback insight extraction.")
            return {
                "summary": "Using local processing due to API reliability issues",
                "key_points": ["Circuit breaker active - temporarily using local processing"],
                "pain_points": ["API reliability issues detected"],
                "feature_requests": ["Will automatically retry Gemini API later"],
                "positive_aspects": ["Basic analysis still available during API issues"]
            }

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.warning(f"Rate limited for insight extraction. Retry after {int(self.rate_limit_reset_time - time.time())} seconds.")
            return {
                "summary": "Rate limit exceeded. Using local processing temporarily.",
                "key_points": ["Rate limit active - temporarily using local processing"],
                "pain_points": ["API rate limits reached"],
                "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                "positive_aspects": ["Basic analysis still available during rate limiting"]
            }

        try:
            start_time = time.time()

            # Process reviews in smaller batches if there are too many
            if len(reviews) > 20:
                logger.info(f"Processing {len(reviews)} reviews in batches for insight extraction")

                # Split reviews into batches of 20
                batches = [reviews[i:i+20] for i in range(0, len(reviews), 20)]

                # Process each batch and combine results
                all_key_points = []
                all_pain_points = []
                all_feature_requests = []
                all_positive_aspects = []
                batch_summaries = []

                for i, batch in enumerate(batches):
                    logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} reviews")

                    # Process this batch
                    batch_result = self._extract_insights_single_batch(batch)

                    # Collect results
                    batch_summaries.append(batch_result.get("summary", ""))
                    all_key_points.extend(batch_result.get("key_points", []))
                    all_pain_points.extend(batch_result.get("pain_points", []))
                    all_feature_requests.extend(batch_result.get("feature_requests", []))
                    all_positive_aspects.extend(batch_result.get("positive_aspects", []))

                    # Add a small delay between batches to avoid rate limiting
                    if i < len(batches) - 1:
                        time.sleep(1)

                # Generate a combined summary
                combined_summary = self._generate_combined_summary(batch_summaries)

                # Remove duplicates
                all_key_points = list(set(all_key_points))
                all_pain_points = list(set(all_pain_points))
                all_feature_requests = list(set(all_feature_requests))
                all_positive_aspects = list(set(all_positive_aspects))

                # Log the array lengths after deduplication
                logger.info(f"After deduplication - key_points: {len(all_key_points)}, " +
                           f"pain_points: {len(all_pain_points)}, " +
                           f"feature_requests: {len(all_feature_requests)}, " +
                           f"positive_aspects: {len(all_positive_aspects)}")

                # If all arrays are empty, add some default content
                if not all_key_points and not all_pain_points and not all_feature_requests and not all_positive_aspects:
                    logger.warning("All insight arrays are empty, adding default content")
                    # Add default content based on the summary
                    if combined_summary:
                        all_key_points = ["No specific key points identified. Please review the summary."]

                        # Try to extract some insights from the summary
                        if "issue" in combined_summary.lower() or "problem" in combined_summary.lower():
                            all_pain_points = ["Issues mentioned in summary: " + combined_summary[:100]]

                        if "request" in combined_summary.lower() or "would like" in combined_summary.lower():
                            all_feature_requests = ["Potential requests mentioned in summary: " + combined_summary[:100]]

                        if "good" in combined_summary.lower() or "great" in combined_summary.lower() or "like" in combined_summary.lower():
                            all_positive_aspects = ["Positive aspects mentioned in summary: " + combined_summary[:100]]

                result = {
                    "summary": combined_summary if combined_summary else "No summary available",
                    "key_points": all_key_points[:10] if all_key_points else ["No key points identified"],  # Limit to top 10
                    "pain_points": all_pain_points[:10] if all_pain_points else ["No specific pain points identified"],
                    "feature_requests": all_feature_requests[:10] if all_feature_requests else ["No specific feature requests identified"],
                    "positive_aspects": all_positive_aspects[:10] if all_positive_aspects else ["No specific positive aspects identified"]
                }

                processing_time = time.time() - start_time
                logger.info(f"Gemini batch insight extraction completed in {processing_time:.2f} seconds for {len(reviews)} reviews")

                return result
            else:
                # Process all reviews in a single batch
                return self._extract_insights_single_batch(reviews)

        except Exception as e:
            logger.error(f"Error in Gemini insight extraction: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

                return {
                    "summary": "Rate limit exceeded. Using local processing temporarily.",
                    "key_points": ["Rate limit active - temporarily using local processing"],
                    "pain_points": ["API rate limits reached"],
                    "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                    "positive_aspects": ["Basic analysis still available during rate limiting"]
                }
            else:
                # For non-rate-limit errors, still increment failure counter but with less weight
                self.consecutive_failures += 0.5

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

                return {
                    "summary": f"Error extracting insights: {str(e)}",
                    "key_points": ["Error occurred during API processing"],
                    "pain_points": ["API processing error encountered"],
                    "feature_requests": ["System will automatically retry later"],
                    "positive_aspects": ["Basic analysis still available"]
                }

    def _extract_insights_single_batch(self, reviews: List[str]) -> Dict[str, Any]:
        """
        Extract insights from a single batch of reviews.
        """
        try:
            start_time = time.time()

            # Prepare the prompt with all reviews
            reviews_text = "\n".join([f"Review {i+1}: {review}" for i, review in enumerate(reviews)])

            prompt = f"""
            Analyze the following product reviews and extract insights. Return a JSON object with:
            - summary: A brief summary of the overall feedback (required, must not be empty)
            - key_points: Array of the most important points mentioned across reviews (required, must contain at least 1 item)
            - pain_points: Array of issues or problems mentioned by users (required, must contain at least 1 item)
            - feature_requests: Array of features or improvements requested by users (required, must contain at least 1 item)
            - positive_aspects: Array of positive aspects mentioned by users (required, must contain at least 1 item)

            IMPORTANT: All arrays must contain at least one item. If you cannot find specific items for a category,
            include a general statement like "No specific pain points identified" as an item in that array.

            Reviews:
            {reviews_text}

            Return only the JSON object without any additional text.
            """

            response = self.model.generate_content(prompt)

            # Log the raw response for debugging
            logger.info(f"Raw Gemini response: {response.text[:500]}...")

            # Extract JSON from response
            try:
                # Try to parse the response text as JSON
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from the text
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1)
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()
                logger.info(f"Extracted JSON text: {text[:500]}...")
                result = json.loads(text)

            # Ensure all required fields exist with default values if missing
            if "summary" not in result or not result["summary"]:
                result["summary"] = "No summary available"
                logger.warning("Summary field missing or empty in Gemini response")

            for field in ["key_points", "pain_points", "feature_requests", "positive_aspects"]:
                if field not in result or not isinstance(result[field], list):
                    result[field] = []
                    logger.warning(f"{field} field missing or not a list in Gemini response")

            # Log the parsed result structure
            logger.info(f"Parsed Gemini result structure: {list(result.keys())}")
            logger.info(f"Array lengths - key_points: {len(result.get('key_points', []))}, " +
                       f"pain_points: {len(result.get('pain_points', []))}, " +
                       f"feature_requests: {len(result.get('feature_requests', []))}, " +
                       f"positive_aspects: {len(result.get('positive_aspects', []))}")

            processing_time = time.time() - start_time
            logger.info(f"Gemini insight extraction completed in {processing_time:.2f} seconds for {len(reviews)} reviews")

            # Reset failure counter on success if it exists
            if hasattr(self, 'consecutive_failures'):
                self.consecutive_failures = 0

            return result

        except Exception as e:
            logger.error(f"Error in single batch insight extraction: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded in single batch. Using fallback for {wait_time} seconds.")

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

                return {
                    "summary": "Rate limit exceeded. Using local processing temporarily.",
                    "key_points": ["Rate limit active - temporarily using local processing"],
                    "pain_points": ["API rate limits reached"],
                    "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                    "positive_aspects": ["Basic analysis still available during rate limiting"]
                }
            else:
                # For non-rate-limit errors, still increment failure counter but with less weight
                self.consecutive_failures += 0.5

                # Check if we should open the circuit breaker
                if self.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()

                return {
                    "summary": f"Error extracting insights: {str(e)}",
                    "key_points": ["Error occurred during API processing"],
                    "pain_points": ["API processing error encountered"],
                    "feature_requests": ["System will automatically retry later"],
                    "positive_aspects": ["Basic analysis still available"]
                }

    def _generate_combined_summary(self, summaries: List[str]) -> str:
        """
        Generate a combined summary from multiple batch summaries.
        """
        if not summaries:
            return "No summaries available."

        if len(summaries) == 1:
            return summaries[0]

        try:
            # Use Gemini to combine summaries
            combined_text = "\n".join([f"Summary {i+1}: {summary}" for i, summary in enumerate(summaries)])

            prompt = f"""
            Combine the following summaries into a single coherent summary that captures the main points.

            {combined_text}

            Return only the combined summary, no additional text.
            """

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Error generating combined summary: {str(e)}")
            # Fall back to concatenating summaries
            return " ".join(summaries)
