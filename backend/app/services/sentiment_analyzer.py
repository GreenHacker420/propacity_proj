import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
import os
import re
import logging
import time
import json
from dotenv import load_dotenv
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        # Initialize Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
        else:
            self.available = False
            logger.warning("Gemini API key not found. Using fallback sentiment analysis.")

        # Cache for sentiment analysis results
        self.sentiment_cache = {}

        # Rate limit tracking
        self.rate_limited = False
        self.rate_limit_reset_time = 0
        self.consecutive_failures = 0
        self.max_retries = 3
        self.backoff_factor = 2
        self.initial_wait_time = 5  # seconds

    async def analyze_sentiment(self, text: str) -> float:
        """
        Analyze the sentiment of the given text using Gemini API.
        Returns a score between -1 (very negative) and 1 (very positive).
        Falls back to local analysis if API is unavailable or rate limited.
        """
        # Check cache first
        if text in self.sentiment_cache:
            return self.sentiment_cache[text]

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback sentiment analysis due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            score = self._local_sentiment_analysis(text)
            self.sentiment_cache[text] = score
            return score

        # Try Gemini API if available
        if self.available:
            try:
                prompt = f"""
                Analyze the sentiment of the following text and provide a score between -1 and 1,
                where -1 is very negative and 1 is very positive. Only return the numerical score.

                Text: {text}
                """

                # Use synchronous call instead of async
                response = self.model.generate_content(prompt)
                score = float(response.text.strip())
                score = max(min(score, 1.0), -1.0)  # Ensure score is between -1 and 1

                # Reset failure counter on success
                self.consecutive_failures = 0

                # Cache the result
                self.sentiment_cache[text] = score
                return score

            except Exception as e:
                logger.error(f"Error analyzing sentiment with Gemini API: {str(e)}")

                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower():
                    self.consecutive_failures += 1
                    wait_time = self._calculate_backoff_time()

                    # Set rate limiting flags
                    self.rate_limited = True
                    self.rate_limit_reset_time = time.time() + wait_time

                    logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

                # Fall back to local analysis
                score = self._local_sentiment_analysis(text)
                self.sentiment_cache[text] = score
                return score
        else:
            # Use local sentiment analysis if Gemini is not available
            score = self._local_sentiment_analysis(text)
            self.sentiment_cache[text] = score
            return score

    def _calculate_backoff_time(self) -> int:
        """Calculate exponential backoff time based on consecutive failures"""
        return min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

    def _local_sentiment_analysis(self, text: str) -> float:
        """
        Simple rule-based sentiment analysis as a fallback when Gemini API is unavailable.
        Returns a score between -1 and 1.
        """
        text = text.lower()

        # Define positive and negative word lists
        positive_words = [
            "good", "great", "excellent", "amazing", "awesome", "fantastic",
            "wonderful", "love", "best", "perfect", "happy", "pleased", "like",
            "enjoy", "satisfied", "impressive", "helpful", "easy", "recommend"
        ]

        negative_words = [
            "bad", "terrible", "awful", "horrible", "poor", "worst", "hate",
            "difficult", "disappointing", "frustrated", "annoying", "useless",
            "slow", "expensive", "problem", "issue", "bug", "crash", "error",
            "fail", "broken", "waste", "confusing", "complicated"
        ]

        # Count positive and negative words
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        # Calculate basic sentiment score
        total = positive_count + negative_count
        if total == 0:
            return 0.0  # Neutral if no sentiment words found

        return (positive_count - negative_count) / total

    async def analyze_sentiment_batch(self, texts: List[str]) -> List[float]:
        """
        Analyze sentiment for a batch of texts more efficiently.
        Returns a list of scores between -1 and 1.
        """
        # Check if we're currently rate limited or Gemini is unavailable
        if not self.available or (self.rate_limited and time.time() < self.rate_limit_reset_time):
            logger.info("Using fallback batch sentiment analysis")
            return [self._local_sentiment_analysis(text) for text in texts]

        # Check cache first and collect uncached texts
        results = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            if text in self.sentiment_cache:
                results.append(self.sentiment_cache[text])
            else:
                results.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)

        # If all texts were cached, return results
        if not uncached_texts:
            return results

        # Process uncached texts in one batch API call
        try:
            # Combine all texts into a single prompt
            combined_text = "\n".join([f"Text {i+1}: {text}" for i, text in enumerate(uncached_texts)])

            prompt = f"""
            Analyze the sentiment of each of the following texts and provide a score between -1 and 1 for each,
            where -1 is very negative and 1 is very positive.

            Return a JSON array of numbers representing the sentiment scores in the same order as the texts.
            Only return the JSON array, nothing else.

            {combined_text}
            """

            # Make a single API call for all texts
            response = self.model.generate_content(prompt)

            # Parse the response
            try:
                # Try to parse as JSON directly
                scores = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                text = response.text.strip()
                if "```" in text:
                    # Extract content from code block
                    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
                    if match:
                        text = match.group(1).strip()
                scores = json.loads(text)

            # Update results and cache
            for i, score in enumerate(scores):
                score = max(min(float(score), 1.0), -1.0)  # Ensure score is between -1 and 1
                original_index = uncached_indices[i]
                results[original_index] = score
                self.sentiment_cache[uncached_texts[i]] = score

            # Reset failure counter on success
            self.consecutive_failures = 0

        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {str(e)}")

            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower():
                self.consecutive_failures += 1
                wait_time = self._calculate_backoff_time()

                # Set rate limiting flags
                self.rate_limited = True
                self.rate_limit_reset_time = time.time() + wait_time

                logger.warning(f"Rate limit exceeded in batch analysis. Using fallback for {wait_time} seconds.")

            # Fall back to local analysis for uncached texts
            for i, text in enumerate(uncached_texts):
                score = self._local_sentiment_analysis(text)
                original_index = uncached_indices[i]
                results[original_index] = score
                self.sentiment_cache[text] = score

        return results

    async def get_sentiment_details(self, text: str) -> Dict[str, Any]:
        """
        Get detailed sentiment analysis including emotion, intensity, and confidence.
        """
        prompt = f"""
        Analyze the sentiment of the following text and provide a detailed analysis in JSON format:
        {{
            "sentiment_score": float,  # between -1 and 1
            "emotion": str,  # primary emotion
            "intensity": float,  # between 0 and 1
            "confidence": float,  # between 0 and 1
            "key_phrases": list[str]  # important phrases that influenced the sentiment
        }}

        Text: {text}
        """

        try:
            # Use synchronous call instead of async
            response = self.model.generate_content(prompt)
            return eval(response.text.strip())  # Convert string to dict
        except Exception as e:
            print(f"Error getting sentiment details: {str(e)}")
            return {
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "intensity": 0.0,
                "confidence": 0.0,
                "key_phrases": []
            }