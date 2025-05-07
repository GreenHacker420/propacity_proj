"""
Gemini API service for faster data processing.
This service provides integration with Google's Gemini API for advanced text analysis.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union
import time
import random
from nltk.sentiment import SentimentIntensityAnalyzer
import concurrent.futures
from functools import partial

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

# Try to import advanced sentiment analyzer
try:
    from ..services.advanced_sentiment import advanced_sentiment_analyzer
    ADVANCED_SENTIMENT_AVAILABLE = True
    logger.info("Advanced sentiment analyzer available for fallback")
except ImportError:
    logger.warning("Advanced sentiment analyzer not available. Using basic fallback.")
    ADVANCED_SENTIMENT_AVAILABLE = False

# Initialize VADER sentiment analyzer for fallback
try:
    vader_analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
    logger.info("VADER sentiment analyzer available for fallback")
except Exception as e:
    logger.warning(f"VADER sentiment analyzer not available: {str(e)}")
    VADER_AVAILABLE = False

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

        # Request throttling
        self.last_request_time = 0
        self.min_request_interval = 0.1  # seconds between requests (adaptive)
        self.request_count = 0
        self.request_window_start = time.time()
        self.max_requests_per_minute = 60  # adjust based on your API limits

        # Performance monitoring
        self.total_api_time = 0
        self.total_api_calls = 0
        self.avg_response_time = 0

        # Circuit breaker pattern
        self.circuit_open = False  # When True, circuit is "open" and we bypass Gemini API completely
        self.circuit_reset_time = 0  # When to try closing the circuit again
        self.failure_threshold = 2  # Number of consecutive failures before opening circuit (reduced from 3)
        self.circuit_reset_timeout = 10 * 60  # 10 minutes - how long to keep circuit open

        # Cache for API responses - use a larger cache size
        self.sentiment_cache = {}
        self.insight_cache = {}
        self.summary_cache = {}  # Cache for combined summaries
        self.cache_size_limit = 10000  # Store up to 10,000 results

        # Cache hit tracking for performance monitoring
        self.cache_hits = 0
        self.cache_misses = 0

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

    def _add_to_cache(self, text: str, result: Dict[str, Any], cache_type: str = "sentiment") -> None:
        """
        Add a result to the specified cache and manage cache size.

        Args:
            text: The text that was analyzed
            result: The analysis result
            cache_type: Type of cache to use ("sentiment", "insight", or "summary")
        """
        # Select the appropriate cache
        if cache_type == "sentiment":
            cache = self.sentiment_cache
        elif cache_type == "insight":
            cache = self.insight_cache
        elif cache_type == "summary":
            cache = self.summary_cache
        else:
            logger.warning(f"Unknown cache type: {cache_type}. Using sentiment cache.")
            cache = self.sentiment_cache

        # Create a cache key based on the text
        # For long texts, use a hash to save memory
        if len(text) > 1000:
            import hashlib
            # Use first 100 chars + hash of full text as key to balance uniqueness and memory usage
            key = text[:100] + "_" + hashlib.md5(text.encode()).hexdigest()
        else:
            key = text

        # Add to cache with timestamp for LRU implementation
        cache[key] = {
            "result": result,
            "timestamp": time.time()
        }

        # Check if cache is too large
        if len(cache) > self.cache_size_limit:
            # Remove 10% of the oldest entries based on timestamp
            remove_count = int(self.cache_size_limit * 0.1)

            # Sort by timestamp (oldest first)
            sorted_keys = sorted(cache.keys(), key=lambda k: cache[k]["timestamp"])
            keys_to_remove = sorted_keys[:remove_count]

            for key in keys_to_remove:
                del cache[key]

            logger.info(f"{cache_type.capitalize()} cache size limit reached. Removed {remove_count} oldest entries.")

    def _get_from_cache(self, text: str, cache_type: str = "sentiment") -> Optional[Dict[str, Any]]:
        """
        Get a result from the specified cache.

        Args:
            text: The text to look up
            cache_type: Type of cache to use ("sentiment", "insight", or "summary")

        Returns:
            The cached result or None if not found
        """
        # Select the appropriate cache
        if cache_type == "sentiment":
            cache = self.sentiment_cache
        elif cache_type == "insight":
            cache = self.insight_cache
        elif cache_type == "summary":
            cache = self.summary_cache
        else:
            logger.warning(f"Unknown cache type: {cache_type}. Using sentiment cache.")
            cache = self.sentiment_cache

        # Create the same key format as used in _add_to_cache
        if len(text) > 1000:
            import hashlib
            key = text[:100] + "_" + hashlib.md5(text.encode()).hexdigest()
        else:
            key = text

        # Check if key exists in cache
        if key in cache:
            self.cache_hits += 1
            # Update timestamp to mark as recently used
            cache[key]["timestamp"] = time.time()
            return cache[key]["result"]

        self.cache_misses += 1
        return None

    def _throttle_requests(self) -> None:
        """
        Throttle API requests to avoid hitting rate limits.
        Implements adaptive throttling based on recent response times and error rates.
        """
        current_time = time.time()

        # Check if we're making too many requests in the current window
        if current_time - self.request_window_start < 60:  # 1-minute window
            if self.request_count >= self.max_requests_per_minute:
                # Wait until the window resets
                sleep_time = 60 - (current_time - self.request_window_start)
                if sleep_time > 0:
                    logger.info(f"Request throttling: waiting {sleep_time:.2f}s to avoid rate limits")
                    time.sleep(sleep_time)
                    # Reset the window
                    self.request_window_start = time.time()
                    self.request_count = 0
        else:
            # Reset the window if it's been more than a minute
            self.request_window_start = current_time
            self.request_count = 0

        # Ensure minimum time between requests
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)

        # Adjust the minimum interval based on recent performance
        if self.total_api_calls > 10:
            # If we're getting a lot of errors, slow down more
            if self.consecutive_failures > 0:
                self.min_request_interval = min(1.0, self.min_request_interval * 1.5)
            # If things are going well, speed up slightly
            elif self.consecutive_failures == 0 and self.min_request_interval > 0.1:
                self.min_request_interval = max(0.1, self.min_request_interval * 0.9)

        # Update tracking variables
        self.last_request_time = time.time()
        self.request_count += 1

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
            "using_local_processing": self.rate_limited or self.circuit_open or not self.available,
            "performance": {
                "avg_response_time": round(self.avg_response_time, 3) if self.total_api_calls > 0 else 0,
                "total_api_calls": self.total_api_calls,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_ratio": round(self.cache_hits / (self.cache_hits + self.cache_misses), 2) if (self.cache_hits + self.cache_misses) > 0 else 0,
                "throttling": {
                    "min_request_interval": round(self.min_request_interval, 3),
                    "requests_per_minute": self.max_requests_per_minute
                }
            },
            "cache_stats": {
                "sentiment_cache_size": len(self.sentiment_cache),
                "insight_cache_size": len(self.insight_cache),
                "summary_cache_size": len(self.summary_cache)
            }
        }

        # Add rate limit information if applicable
        if self.rate_limited and current_time < self.rate_limit_reset_time:
            status["rate_limit_reset_in"] = int(self.rate_limit_reset_time - current_time)

        # Add circuit breaker information if applicable
        if self.circuit_open:
            status["circuit_reset_in"] = int(self.circuit_reset_time - current_time)

        # Add consecutive failures information
        status["consecutive_failures"] = self.consecutive_failures

        return status

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using Gemini API.

        Args:
            text: The text to analyze

        Returns:
            Dictionary with sentiment analysis results
        """
        # Check for any condition that would prevent API use and return fallback immediately
        if not self.available:
            logger.warning("Gemini API not available for sentiment analysis")
            return self._local_sentiment_analysis(text)

        # Check cache first using the new cache method
        cached_result = self._get_from_cache(text, "sentiment")
        if cached_result:
            return cached_result

        # Combined check for circuit breaker and rate limiting
        circuit_open = self._check_circuit_breaker()
        rate_limited = self.rate_limited and time.time() < self.rate_limit_reset_time

        if circuit_open or rate_limited:
            if circuit_open:
                logger.info("Circuit breaker open. Using fallback sentiment analysis.")
            else:
                logger.info(f"Using fallback sentiment analysis due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")

            # Use local sentiment analysis as fallback
            score = self._local_sentiment_analysis(text)
            self.sentiment_cache[text] = score
            return score

        try:
            start_time = time.time()

            # Apply throttling before making the API call
            self._throttle_requests()

            # Improved prompt with explicit JSON formatting instructions
            prompt = f"""
            Analyze the sentiment of the following text and return a valid JSON object with:
            - "score": a float between 0 (negative) and 1 (positive)
            - "label": one of "POSITIVE", "NEGATIVE", or "NEUTRAL"
            - "confidence": a float between 0 and 1 indicating confidence in the analysis

            Example of expected format:
            {{"score": 0.8, "label": "POSITIVE", "confidence": 0.9}}

            Text: "{text}"

            IMPORTANT: Return ONLY the JSON object with no markdown formatting, no ```json tags, and no other text.
            Use double quotes for all keys and string values.
            """

            # Track API call performance
            api_start_time = time.time()
            response = self.model.generate_content(prompt)
            api_time = time.time() - api_start_time

            # Update performance metrics
            self.total_api_time += api_time
            self.total_api_calls += 1
            self.avg_response_time = self.total_api_time / self.total_api_calls

            # Log performance metrics periodically
            if self.total_api_calls % 10 == 0:
                logger.info(f"Gemini API performance: avg_time={self.avg_response_time:.2f}s, " +
                           f"calls={self.total_api_calls}, cache_hits={self.cache_hits}, " +
                           f"cache_misses={self.cache_misses}")

            # Log this specific call's performance
            logger.info(f"Gemini API call for sentiment analysis took {api_time:.2f}s")

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

            # Cache the result with the new method
            self._add_to_cache(text, result, "sentiment")

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

            # Use local sentiment analysis as fallback
            score = self._local_sentiment_analysis(text)
            self._add_to_cache(text, score, "sentiment")
            return score

    def _parallel_local_sentiment_analysis(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Perform local sentiment analysis in parallel for multiple reviews.

        Args:
            reviews: List of review texts to analyze

        Returns:
            List of dictionaries with sentiment analysis results
        """
        start_time = time.time()
        logger.info(f"Starting parallel sentiment analysis for {len(reviews)} reviews")

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
            results = list(executor.map(self._local_sentiment_analysis, reviews))

        processing_time = time.time() - start_time
        logger.info(f"Parallel sentiment analysis completed in {processing_time:.2f} seconds for {len(reviews)} reviews")

        return results

    def _local_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """
        Perform local sentiment analysis when Gemini API is unavailable.

        Args:
            text: The text to analyze

        Returns:
            Dictionary with sentiment analysis results
        """
        # Check cache first for faster processing using the new method
        cached_result = self._get_from_cache(text, "sentiment")
        if cached_result:
            return cached_result

        # Use VADER sentiment analyzer for speed (skip advanced analyzer for performance)
        if VADER_AVAILABLE:
            try:
                sentiment_scores = vader_analyzer.polarity_scores(text)
                compound_score = sentiment_scores['compound']

                # Convert compound score from [-1, 1] to [0, 1]
                normalized_score = (compound_score + 1) / 2

                # Determine sentiment label
                if compound_score >= 0.05:
                    label = "POSITIVE"
                elif compound_score <= -0.05:
                    label = "NEGATIVE"
                else:
                    label = "NEUTRAL"

                # Calculate confidence based on the magnitude of the compound score
                confidence = abs(compound_score)

                result = {
                    "score": normalized_score,
                    "label": label,
                    "confidence": confidence
                }

                # Cache the result with the new method
                self._add_to_cache(text, result, "sentiment")

                return result
            except Exception as e:
                logger.error(f"Error using VADER sentiment analyzer: {str(e)}")
                # Fall back to basic sentiment

        # Basic fallback if all else fails
        result = {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}
        self._add_to_cache(text, result, "sentiment")
        return result

    def analyze_reviews(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple reviews in batch for faster processing.

        Args:
            reviews: List of review texts to analyze

        Returns:
            List of dictionaries with analysis results
        """
        # Early check for circuit breaker or rate limiting to avoid unnecessary processing
        if not self.available:
            logger.warning("Gemini API not available for review analysis")
            return self._parallel_local_sentiment_analysis(reviews)

        # Check if circuit breaker is open
        if self._check_circuit_breaker():
            logger.info("Circuit breaker open. Using fallback batch sentiment analysis.")
            return self._parallel_local_sentiment_analysis(reviews)

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback sentiment analysis due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            return self._parallel_local_sentiment_analysis(reviews)

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

        # Process reviews in larger batches for better performance
        if len(uncached_reviews) > 100:
            logger.info(f"Processing {len(uncached_reviews)} reviews in batches for sentiment analysis")

            # Split reviews into batches of 100 (increased from 20)
            batches = [uncached_reviews[i:i+100] for i in range(0, len(uncached_reviews), 100)]
            batch_indices = [uncached_indices[i:i+100] for i in range(0, len(uncached_indices), 100)]

            # Check circuit breaker state once before processing all batches
            circuit_open = self._check_circuit_breaker()
            rate_limited = self.rate_limited and time.time() < self.rate_limit_reset_time

            # If circuit is open or rate limited, process all reviews with fallback at once
            if circuit_open or rate_limited:
                if circuit_open:
                    logger.info(f"Circuit breaker open. Using fallback for all {len(reviews)} reviews at once")
                else:
                    logger.info(f"Rate limited. Using fallback for all {len(reviews)} reviews at once")

                # Create fallback results for all reviews at once
                fallback_results = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in reviews]

                # No need to process batches, just return the fallback results
                return fallback_results

            # Process each batch normally if circuit is closed and not rate limited
            for i, (batch, indices) in enumerate(zip(batches, batch_indices)):
                logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} reviews")

                # Check if circuit breaker is open before processing this batch (in case it opened during processing)
                if self._check_circuit_breaker():
                    logger.info(f"Circuit breaker open. Using fallback for batch {i+1}/{len(batches)}")
                    batch_results = self._parallel_local_sentiment_analysis(batch)
                # Check if we're currently rate limited
                elif self.rate_limited and time.time() < self.rate_limit_reset_time:
                    logger.info(f"Rate limited. Using fallback for batch {i+1}/{len(batches)}")
                    batch_results = self._parallel_local_sentiment_analysis(batch)
                else:
                    # Process this batch with Gemini API
                    batch_results = self._analyze_reviews_single_batch(batch)

                # Update results and cache
                for j, result in enumerate(batch_results):
                    original_index = indices[j]
                    results[original_index] = result
                    self._add_to_cache(batch[j], result)

                # Add a small delay between batches to avoid rate limiting
                if i < len(batches) - 1 and not self._check_circuit_breaker() and not self.rate_limited:
                    time.sleep(1)

            return results
        else:
            # Check if circuit breaker is open before processing
            if self._check_circuit_breaker():
                logger.info(f"Circuit breaker open. Using fallback for single batch with {len(uncached_reviews)} reviews")
                batch_results = self._parallel_local_sentiment_analysis(uncached_reviews)
            # Check if we're currently rate limited
            elif self.rate_limited and time.time() < self.rate_limit_reset_time:
                logger.info(f"Rate limited. Using fallback for single batch with {len(uncached_reviews)} reviews")
                batch_results = self._parallel_local_sentiment_analysis(uncached_reviews)
            else:
                # Process all uncached reviews in a single batch with Gemini API
                batch_results = self._analyze_reviews_single_batch(uncached_reviews)

            # Update results and cache
            for i, result in enumerate(batch_results):
                original_index = uncached_indices[i]
                results[original_index] = result
                self._add_to_cache(uncached_reviews[i], result)

            return results

    def _analyze_reviews_single_batch(self, reviews: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze a single batch of reviews with optimized prompt for faster processing.
        """
        try:
            start_time = time.time()

            # Prepare the prompt with all reviews - use a more compact format
            reviews_text = "\n".join([f"{i+1}:{review}" for i, review in enumerate(reviews)])

            # Apply throttling before making the API call
            self._throttle_requests()

            # Improved prompt for more reliable JSON responses
            prompt = f"""
            Analyze sentiment of these reviews. Return a valid JSON array with objects containing:
            "score" (float 0-1, negative to positive), "label" (string: "POSITIVE"/"NEGATIVE"/"NEUTRAL"), "confidence" (float 0-1).

            Example of expected format:
            [
              {{"score": 0.8, "label": "POSITIVE", "confidence": 0.9}},
              {{"score": 0.2, "label": "NEGATIVE", "confidence": 0.7}}
            ]

            Reviews:
            {reviews_text}

            IMPORTANT: Return ONLY the JSON array with no markdown formatting, no ```json tags, and no other text.
            Use double quotes for all keys and string values.
            """

            # Track API call performance
            api_start_time = time.time()
            response = self.model.generate_content(prompt)
            api_time = time.time() - api_start_time

            # Update performance metrics
            self.total_api_time += api_time
            self.total_api_calls += 1
            self.avg_response_time = self.total_api_time / self.total_api_calls

            # Log performance for batch processing
            logger.info(f"Gemini API batch call for {len(reviews)} reviews took {api_time:.2f}s " +
                       f"({api_time/len(reviews):.4f}s per review)")

            # Log the raw response for debugging
            logger.info(f"Raw batch sentiment response (first 200 chars): {response.text[:200]}...")

            # Extract JSON from response with improved error handling
            try:
                # Try to parse the response text as JSON directly
                results = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}. Attempting to extract JSON from text.")
                # If parsing fails, try to extract JSON from the text with more robust handling
                text = response.text.strip()

                # Handle markdown code blocks
                if "```" in text:
                    # Extract content between first ``` and last ```
                    parts = text.split("```")
                    for i, part in enumerate(parts):
                        if i > 0 and i < len(parts) - 1:  # Skip first and last parts (outside ```)
                            # Remove "json" if it's at the start of the code block
                            if part.startswith("json"):
                                part = part[4:].strip()
                            elif part.startswith("JSON"):
                                part = part[4:].strip()

                            # Try to parse this part
                            try:
                                results = json.loads(part.strip())
                                logger.info("Successfully extracted JSON from code block")
                                break
                            except json.JSONDecodeError:
                                continue
                else:
                    # Try to find array brackets if no code blocks
                    try:
                        # Find the first [ and last ]
                        start_idx = text.find('[')
                        end_idx = text.rfind(']')

                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            json_text = text[start_idx:end_idx+1]
                            results = json.loads(json_text)
                            logger.info("Successfully extracted JSON array using bracket detection")
                        else:
                            raise ValueError("Could not find valid JSON array brackets")
                    except Exception as bracket_error:
                        logger.error(f"Failed to extract JSON using bracket detection: {str(bracket_error)}")
                        # Last resort - try to clean up the text and parse again
                        clean_text = text.replace("'", '"')  # Replace single quotes with double quotes
                        try:
                            results = json.loads(clean_text)
                            logger.info("Successfully parsed JSON after quote replacement")
                        except json.JSONDecodeError:
                            logger.error(f"All JSON extraction methods failed. Response text: {text[:500]}...")
                            # Fall back to local processing
                            raise ValueError("Failed to parse JSON response from Gemini API")

            processing_time = time.time() - start_time
            logger.info(f"Gemini batch review analysis completed in {processing_time:.2f} seconds for {len(reviews)} reviews")

            # Reset failure counter on success
            self.consecutive_failures = 0

            return results

        except ValueError as ve:
            # Handle specific ValueError from our JSON parsing logic
            logger.error(f"JSON parsing error in batch review analysis: {str(ve)}")
            self.consecutive_failures += 0.5

            # Check if we should open the circuit breaker
            if self.consecutive_failures >= self.failure_threshold:
                self._open_circuit()

            # Return fallback results
            return self._parallel_local_sentiment_analysis(reviews)

        except json.JSONDecodeError as je:
            # Handle JSON decode errors specifically
            logger.error(f"JSON decode error in batch review analysis: {str(je)}")
            self.consecutive_failures += 0.5

            # Check if we should open the circuit breaker
            if self.consecutive_failures >= self.failure_threshold:
                self._open_circuit()

            # Return fallback results
            return self._parallel_local_sentiment_analysis(reviews)

        except Exception as e:
            logger.error(f"Error in Gemini batch review analysis: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
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

            # Log detailed error information for debugging
            import traceback
            logger.error(f"Detailed error in batch review analysis: {traceback.format_exc()}")

            # Return fallback results
            return self._parallel_local_sentiment_analysis(reviews)

    def extract_insights(self, reviews: List[str]) -> Dict[str, Any]:
        """
        Extract insights from a collection of reviews.

        Args:
            reviews: List of review texts

        Returns:
            Dictionary with insights
        """
        # Early check for circuit breaker or rate limiting to avoid unnecessary processing
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

            # Process reviews in optimized batches if there are too many
            if len(reviews) > 50:  # Increased batch size from 20 to 50 for better efficiency
                logger.info(f"Processing {len(reviews)} reviews in batches for insight extraction")

                # Calculate optimal batch size based on review length
                avg_review_length = sum(len(review) for review in reviews) / len(reviews)

                # Adjust batch size based on average review length
                # Shorter reviews can be processed in larger batches
                if avg_review_length < 100:
                    batch_size = 100  # Very short reviews
                elif avg_review_length < 200:
                    batch_size = 75   # Short reviews
                elif avg_review_length < 500:
                    batch_size = 50   # Medium reviews
                else:
                    batch_size = 30   # Long reviews

                logger.info(f"Using batch size of {batch_size} for reviews with avg length {avg_review_length:.1f} chars")

                # Split reviews into optimized batches
                batches = [reviews[i:i+batch_size] for i in range(0, len(reviews), batch_size)]

                # Process each batch and combine results
                all_key_points = []
                all_pain_points = []
                all_feature_requests = []
                all_positive_aspects = []
                batch_summaries = []

                # Check circuit breaker state and rate limit status once before processing
                circuit_open = self._check_circuit_breaker()
                rate_limited = self.rate_limited and time.time() < self.rate_limit_reset_time

                # If circuit is open or rate limited, return fallback insights immediately
                if circuit_open or rate_limited:
                    if circuit_open:
                        logger.info(f"Circuit breaker open. Using fallback insights for all {len(reviews)} reviews at once")
                        return {
                            "summary": "Using local processing due to API reliability issues",
                            "key_points": ["Circuit breaker active - temporarily using local processing"],
                            "pain_points": ["API reliability issues detected"],
                            "feature_requests": ["Will automatically retry Gemini API later"],
                            "positive_aspects": ["Basic analysis still available during API issues"]
                        }
                    else:
                        logger.info(f"Rate limited. Using fallback insights for all {len(reviews)} reviews at once")
                        return {
                            "summary": "Rate limit exceeded. Using local processing temporarily.",
                            "key_points": ["Rate limit active - temporarily using local processing"],
                            "pain_points": ["API rate limits reached"],
                            "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                            "positive_aspects": ["Basic analysis still available during rate limiting"]
                        }

                # Process each batch normally if circuit is closed and not rate limited
                for i, batch in enumerate(batches):
                    logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} reviews")

                    # Check if circuit breaker is open before processing this batch (in case it opened during processing)
                    if self._check_circuit_breaker():
                        logger.info(f"Circuit breaker open. Using fallback for batch {i+1}/{len(batches)}")
                        batch_result = {
                            "summary": "Using local processing due to API reliability issues",
                            "key_points": ["Circuit breaker active - temporarily using local processing"],
                            "pain_points": ["API reliability issues detected"],
                            "feature_requests": ["Will automatically retry Gemini API later"],
                            "positive_aspects": ["Basic analysis still available during API issues"]
                        }
                    # Check if we're currently rate limited
                    elif self.rate_limited and time.time() < self.rate_limit_reset_time:
                        logger.info(f"Rate limited. Using fallback for batch {i+1}/{len(batches)}")
                        batch_result = {
                            "summary": "Rate limit exceeded. Using local processing temporarily.",
                            "key_points": ["Rate limit active - temporarily using local processing"],
                            "pain_points": ["API rate limits reached"],
                            "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                            "positive_aspects": ["Basic analysis still available during rate limiting"]
                        }
                    else:
                        # Process this batch with Gemini API
                        batch_result = self._extract_insights_single_batch(batch)

                    # Collect results
                    batch_summaries.append(batch_result.get("summary", ""))
                    all_key_points.extend(batch_result.get("key_points", []))
                    all_pain_points.extend(batch_result.get("pain_points", []))
                    all_feature_requests.extend(batch_result.get("feature_requests", []))
                    all_positive_aspects.extend(batch_result.get("positive_aspects", []))

                    # Add a small delay between batches to avoid rate limiting
                    if i < len(batches) - 1 and not self._check_circuit_breaker() and not self.rate_limited:
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
                # Check if circuit breaker is open before processing
                if self._check_circuit_breaker():
                    logger.info(f"Circuit breaker open. Using fallback for single batch with {len(reviews)} reviews")
                    return {
                        "summary": "Using local processing due to API reliability issues",
                        "key_points": ["Circuit breaker active - temporarily using local processing"],
                        "pain_points": ["API reliability issues detected"],
                        "feature_requests": ["Will automatically retry Gemini API later"],
                        "positive_aspects": ["Basic analysis still available during API issues"]
                    }
                # Check if we're currently rate limited
                elif self.rate_limited and time.time() < self.rate_limit_reset_time:
                    logger.info(f"Rate limited. Using fallback for single batch with {len(reviews)} reviews")
                    return {
                        "summary": "Rate limit exceeded. Using local processing temporarily.",
                        "key_points": ["Rate limit active - temporarily using local processing"],
                        "pain_points": ["API rate limits reached"],
                        "feature_requests": ["Will automatically retry Gemini API when limits reset"],
                        "positive_aspects": ["Basic analysis still available during rate limiting"]
                    }
                else:
                    # Process all reviews in a single batch with Gemini API
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

            # Check if we have this exact set of reviews cached
            reviews_combined = "\n".join(reviews)
            cached_insights = self._get_from_cache(reviews_combined, "insight")
            if cached_insights:
                logger.info(f"Using cached insights for {len(reviews)} reviews")
                return cached_insights

            # Apply throttling before making the API call
            self._throttle_requests()

            # Improved prompt for more reliable JSON responses
            prompt = f"""
            Analyze the following product reviews and extract insights. Return a valid JSON object with:
            - "summary": A brief summary of the overall feedback (required, must not be empty)
            - "key_points": Array of the most important points mentioned across reviews (required, must contain at least 1 item)
            - "pain_points": Array of issues or problems mentioned by users (required, must contain at least 1 item)
            - "feature_requests": Array of features or improvements requested by users (required, must contain at least 1 item)
            - "positive_aspects": Array of positive aspects mentioned by users (required, must contain at least 1 item)

            Example of expected format:
            {{
              "summary": "Overall, customers are satisfied with the product but have some concerns about durability.",
              "key_points": ["Good value for money", "Easy to use interface"],
              "pain_points": ["Battery life is too short", "Customer service is slow to respond"],
              "feature_requests": ["Add water resistance", "Include more color options"],
              "positive_aspects": ["Fast shipping", "High quality materials"]
            }}

            IMPORTANT:
            1. All arrays must contain at least one item. If you cannot find specific items for a category,
               include a general statement like "No specific pain points identified" as an item in that array.
            2. Return ONLY the JSON object with no markdown formatting, no ```json tags, and no other text.
            3. Use double quotes for all keys and string values.
            4. Be concise in your summary and limit each array to at most 10 items.

            Reviews:
            {reviews_text}
            """

            # Track API call performance
            api_start_time = time.time()
            response = self.model.generate_content(prompt)
            api_time = time.time() - api_start_time

            # Update performance metrics
            self.total_api_time += api_time
            self.total_api_calls += 1
            self.avg_response_time = self.total_api_time / self.total_api_calls

            # Log performance for insight extraction
            logger.info(f"Gemini API insight extraction for {len(reviews)} reviews took {api_time:.2f}s " +
                       f"({api_time/len(reviews):.4f}s per review)")

            # Log the raw response for debugging
            logger.info(f"Raw Gemini insight response (first 200 chars): {response.text[:200]}...")

            # Extract JSON from response with improved error handling
            try:
                # Try to parse the response text as JSON directly
                result = json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error in insights: {str(e)}. Attempting to extract JSON from text.")
                # If parsing fails, try to extract JSON from the text with more robust handling
                text = response.text.strip()

                # Handle markdown code blocks
                if "```" in text:
                    # Extract content between first ``` and last ```
                    parts = text.split("```")
                    for i, part in enumerate(parts):
                        if i > 0 and i < len(parts) - 1:  # Skip first and last parts (outside ```)
                            # Remove "json" if it's at the start of the code block
                            if part.startswith("json"):
                                part = part[4:].strip()
                            elif part.startswith("JSON"):
                                part = part[4:].strip()

                            # Try to parse this part
                            try:
                                result = json.loads(part.strip())
                                logger.info("Successfully extracted JSON from code block in insights")
                                break
                            except json.JSONDecodeError:
                                continue
                else:
                    # Try to find object brackets if no code blocks
                    try:
                        # Find the first { and last }
                        start_idx = text.find('{')
                        end_idx = text.rfind('}')

                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            json_text = text[start_idx:end_idx+1]
                            result = json.loads(json_text)
                            logger.info("Successfully extracted JSON object using bracket detection in insights")
                        else:
                            raise ValueError("Could not find valid JSON object brackets")
                    except Exception as bracket_error:
                        logger.error(f"Failed to extract JSON using bracket detection in insights: {str(bracket_error)}")
                        # Last resort - try to clean up the text and parse again
                        clean_text = text.replace("'", '"')  # Replace single quotes with double quotes
                        try:
                            result = json.loads(clean_text)
                            logger.info("Successfully parsed JSON after quote replacement in insights")
                        except json.JSONDecodeError:
                            logger.error(f"All JSON extraction methods failed for insights. Response text: {text[:500]}...")
                            # Fall back to a default structure
                            raise ValueError("Failed to parse JSON response from Gemini API for insights")

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

            # Cache the insights result
            reviews_combined = "\n".join(reviews)
            self._add_to_cache(reviews_combined, result, "insight")

            return result

        except ValueError as ve:
            # Handle specific ValueError from our JSON parsing logic
            logger.error(f"JSON parsing error in insight extraction: {str(ve)}")
            self.consecutive_failures += 0.5

            # Check if we should open the circuit breaker
            if self.consecutive_failures >= self.failure_threshold:
                self._open_circuit()

            return {
                "summary": f"Error parsing insights: {str(ve)}",
                "key_points": ["JSON parsing error occurred"],
                "pain_points": ["Unable to process API response format"],
                "feature_requests": ["System will automatically retry with improved parsing"],
                "positive_aspects": ["Basic analysis still available"]
            }

        except json.JSONDecodeError as je:
            # Handle JSON decode errors specifically
            logger.error(f"JSON decode error in insight extraction: {str(je)}")
            self.consecutive_failures += 0.5

            # Check if we should open the circuit breaker
            if self.consecutive_failures >= self.failure_threshold:
                self._open_circuit()

            return {
                "summary": "Error processing insights due to invalid JSON format",
                "key_points": ["JSON format error detected"],
                "pain_points": ["API returned improperly formatted data"],
                "feature_requests": ["System will automatically retry with improved parsing"],
                "positive_aspects": ["Basic analysis still available"]
            }

        except Exception as e:
            logger.error(f"Error in single batch insight extraction: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded in insight extraction. Using fallback for {wait_time} seconds.")

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

                # Log detailed error information for debugging
                import traceback
                logger.error(f"Detailed error in insight extraction: {traceback.format_exc()}")

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

        # Filter out empty or invalid summaries
        valid_summaries = [s for s in summaries if s and isinstance(s, str) and len(s.strip()) > 0]

        if not valid_summaries:
            return "No valid summaries available."

        if len(valid_summaries) == 1:
            return valid_summaries[0]

        # Create a cache key from the summaries
        summaries_key = "||".join(valid_summaries)

        # Check if we have this combination cached
        cached_summary = self._get_from_cache(summaries_key, "summary")
        if cached_summary:
            logger.info(f"Using cached combined summary for {len(valid_summaries)} summaries")
            return cached_summary

        # Check if circuit breaker is open or rate limited before making API call
        if self._check_circuit_breaker() or (self.rate_limited and time.time() < self.rate_limit_reset_time):
            logger.info("Circuit breaker open or rate limited. Using local summary combination.")
            # Simple concatenation with deduplication
            combined = " ".join(valid_summaries)
            # Limit length to avoid excessively long summaries
            if len(combined) > 1000:
                combined = combined[:997] + "..."
            # Cache the result
            self._add_to_cache(summaries_key, combined, "summary")
            return combined

        try:
            # Apply throttling before making the API call
            self._throttle_requests()

            # Use Gemini to combine summaries with improved prompt
            combined_text = "\n".join([f"Summary {i+1}: {summary}" for i, summary in enumerate(valid_summaries)])

            prompt = f"""
            Combine these {len(valid_summaries)} summaries into a single coherent summary (max 250 words) that captures the main points.
            Focus on common themes and important insights across all summaries.

            {combined_text}

            IMPORTANT: Return only the combined summary text with no additional commentary, no introduction, and no markdown formatting.
            """

            # Track API call performance
            api_start_time = time.time()
            response = self.model.generate_content(prompt)
            api_time = time.time() - api_start_time

            # Update performance metrics
            self.total_api_time += api_time
            self.total_api_calls += 1
            self.avg_response_time = self.total_api_time / self.total_api_calls

            # Log performance for summary generation
            logger.info(f"Gemini API summary combination took {api_time:.2f}s for {len(valid_summaries)} summaries")

            combined_summary = response.text.strip()

            # Cache the result
            self._add_to_cache(summaries_key, combined_summary, "summary")

            # Verify we got a reasonable response
            if not combined_summary or len(combined_summary) < 10:
                logger.warning("Received empty or very short combined summary from Gemini API")
                # Fall back to concatenating summaries
                combined = " ".join(valid_summaries)
                # Limit length
                if len(combined) > 1000:
                    combined = combined[:997] + "..."
                # Cache the fallback result
                self._add_to_cache(summaries_key, combined, "summary")
                return combined

            return combined_summary

        except Exception as e:
            logger.error(f"Error generating combined summary: {str(e)}")
            # Fall back to concatenating summaries with length limit
            combined = " ".join(valid_summaries)
            if len(combined) > 1000:
                combined = combined[:997] + "..."
            # Cache the error fallback result
            self._add_to_cache(summaries_key, combined, "summary")
            return combined
