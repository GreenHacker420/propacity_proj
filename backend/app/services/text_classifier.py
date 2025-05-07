import google.generativeai as genai
from typing import List, Dict, Any, Optional
import os
import re
import json
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class TextClassifier:
    def __init__(self):
        # Initialize Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
        else:
            self.available = False
            logger.warning("Gemini API key not found. Using fallback text classification.")

        # Cache for classification and keyword extraction results
        self.classification_cache = {}
        self.keyword_cache = {}

        # Rate limit tracking
        self.rate_limited = False
        self.rate_limit_reset_time = 0
        self.consecutive_failures = 0
        self.max_retries = 3
        self.backoff_factor = 2
        self.initial_wait_time = 5  # seconds

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

    def _calculate_backoff_time(self) -> int:
        """Calculate exponential backoff time based on consecutive failures"""
        return min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

    def _rule_based_classification(self, text: str) -> str:
        """
        Simple rule-based classification as a fallback when Gemini API is unavailable.
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
        Simple rule-based keyword extraction as a fallback when Gemini API is unavailable.
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

    async def classify_feedback(self, text: str) -> str:
        """
        Classify the feedback into one of the following categories:
        - pain_point: User is reporting an issue or problem
        - feature_request: User is requesting a new feature
        - positive_feedback: User is providing positive feedback

        Falls back to rule-based classification if API is unavailable or rate limited.
        """
        # Check cache first
        if text in self.classification_cache:
            return self.classification_cache[text]

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback classification due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            category = self._rule_based_classification(text)
            self.classification_cache[text] = category
            return category

        # Try Gemini API if available
        if self.available:
            try:
                prompt = f"""
                Classify the following feedback into exactly one of these categories:
                - pain_point: User is reporting an issue or problem
                - feature_request: User is requesting a new feature
                - positive_feedback: User is providing positive feedback

                Only return the category name, nothing else.

                Feedback: {text}
                """

                # Use synchronous call instead of async
                response = self.model.generate_content(prompt)
                category = response.text.strip().lower()

                # Validate category
                valid_categories = ["pain_point", "feature_request", "positive_feedback"]
                if category not in valid_categories:
                    category = "positive_feedback"  # Default if classification fails

                # Reset failure counter on success
                self.consecutive_failures = 0

                # Cache the result
                self.classification_cache[text] = category
                return category

            except Exception as e:
                logger.error(f"Error classifying feedback with Gemini API: {str(e)}")

                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower():
                    self.consecutive_failures += 1
                    wait_time = self._calculate_backoff_time()

                    # Set rate limiting flags
                    self.rate_limited = True
                    self.rate_limit_reset_time = time.time() + wait_time

                    logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

                # Fall back to rule-based classification
                category = self._rule_based_classification(text)
                self.classification_cache[text] = category
                return category
        else:
            # Use rule-based classification if Gemini is not available
            category = self._rule_based_classification(text)
            self.classification_cache[text] = category
            return category

    async def extract_keywords(self, text: str) -> List[str]:
        """
        Extract key phrases or words from the text that are relevant to the feedback.
        Falls back to rule-based extraction if API is unavailable or rate limited.
        """
        # Check cache first
        if text in self.keyword_cache:
            return self.keyword_cache[text]

        # Check if we're currently rate limited
        if self.rate_limited and time.time() < self.rate_limit_reset_time:
            logger.info(f"Using fallback keyword extraction due to rate limiting (resets in {int(self.rate_limit_reset_time - time.time())} seconds)")
            keywords = self._rule_based_keyword_extraction(text)
            self.keyword_cache[text] = keywords
            return keywords

        # Try Gemini API if available
        if self.available:
            try:
                prompt = f"""
                Extract the most important keywords or phrases from the following text.
                Return them as a comma-separated list, with no additional text.
                Focus on terms that indicate the main topic, issue, or feature being discussed.

                Text: {text}
                """

                # Use synchronous call instead of async
                response = self.model.generate_content(prompt)
                keywords = [k.strip() for k in response.text.strip().split(",")]

                # Reset failure counter on success
                self.consecutive_failures = 0

                # Cache the result
                self.keyword_cache[text] = keywords
                return keywords

            except Exception as e:
                logger.error(f"Error extracting keywords with Gemini API: {str(e)}")

                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower():
                    self.consecutive_failures += 1
                    wait_time = self._calculate_backoff_time()

                    # Set rate limiting flags
                    self.rate_limited = True
                    self.rate_limit_reset_time = time.time() + wait_time

                    logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

                # Fall back to rule-based keyword extraction
                keywords = self._rule_based_keyword_extraction(text)
                self.keyword_cache[text] = keywords
                return keywords
        else:
            # Use rule-based keyword extraction if Gemini is not available
            keywords = self._rule_based_keyword_extraction(text)
            self.keyword_cache[text] = keywords
            return keywords

    async def get_feedback_details(self, text: str) -> Dict[str, Any]:
        """
        Get detailed analysis of the feedback including classification, keywords,
        and additional context.
        """
        prompt = f"""
        Analyze the following feedback and provide a detailed analysis in JSON format:
        {{
            "category": str,  # pain_point, feature_request, or positive_feedback
            "keywords": list[str],  # important keywords or phrases
            "context": str,  # brief explanation of the feedback
            "severity": float,  # between 0 and 1, indicating how critical the feedback is
            "suggested_actions": list[str]  # potential actions to address the feedback
        }}

        Feedback: {text}
        """

        try:
            # Use synchronous call instead of async
            response = self.model.generate_content(prompt)
            return eval(response.text.strip())  # Convert string to dict
        except Exception as e:
            print(f"Error getting feedback details: {str(e)}")
            return {
                "category": "positive_feedback",
                "keywords": [],
                "context": "",
                "severity": 0.0,
                "suggested_actions": []
            }

    async def classify_feedback_batch(self, texts: List[str]) -> List[str]:
        """
        Classify a batch of feedback texts.
        Returns a list of categories.
        """
        results = []
        for text in texts:
            category = await self.classify_feedback(text)
            results.append(category)
        return results

    async def extract_keywords_batch(self, texts: List[str]) -> List[List[str]]:
        """
        Extract keywords from a batch of texts.
        Returns a list of keyword lists.
        """
        results = []
        for text in texts:
            keywords = await self.extract_keywords(text)
            results.append(keywords)
        return results