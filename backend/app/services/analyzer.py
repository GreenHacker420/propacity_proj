import re
import random
from typing import List, Dict, Any
import logging
import torch
import nltk
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os

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
    def __init__(self):
        # Keywords for classification
        self.pain_point_keywords = {'crash', 'error', 'bug', 'issue', 'problem', 'fail', 'slow', 'broken', 'bad', 'terrible', 'awful', 'horrible'}
        self.feature_request_keywords = {'add', 'implement', 'feature', 'request', 'suggest', 'need', 'want', 'would like', 'could use', 'should have'}

        # Initialize NLTK components
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

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

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text using advanced NLP techniques.

        Args:
            text: The text to analyze

        Returns:
            Dictionary with sentiment score, sentiment label, category, and keywords
        """
        # Clean the text
        cleaned_text = self.clean_text(text)

        # Sentiment analysis using Hugging Face model if available
        if self.sentiment_model and text.strip():
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

            except Exception as e:
                logger.error(f"Error in sentiment analysis: {str(e)}")
                # Fall back to simple sentiment analysis
                sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)
        else:
            # Fall back to simple sentiment analysis
            sentiment_score, sentiment_label = self._simple_sentiment_analysis(cleaned_text)

        # Extract keywords
        keywords = self.extract_keywords(cleaned_text)

        # Classify feedback
        category = self.classify_feedback(cleaned_text)

        return {
            "sentiment_score": float(sentiment_score),  # Ensure it's a Python float
            "sentiment_label": sentiment_label,
            "category": category,
            "keywords": keywords
        }

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

    def generate_summary(self, reviews: List[Dict]) -> Dict:
        """
        Generate a summary of the analyzed reviews.

        Args:
            reviews: List of analyzed review dictionaries

        Returns:
            Dictionary with pain points, feature requests, positive feedback, and suggested priorities
        """
        # Group reviews by category
        pain_points = []
        feature_requests = []
        positive_feedback = []

        for review in reviews:
            if review["category"] == "pain_point":
                pain_points.append(review)
            elif review["category"] == "feature_request":
                feature_requests.append(review)
            else:
                positive_feedback.append(review)

        # Sort by sentiment score (ascending for pain points, descending for others)
        pain_points.sort(key=lambda x: x["sentiment_score"])
        feature_requests.sort(key=lambda x: x["sentiment_score"], reverse=True)
        positive_feedback.sort(key=lambda x: x["sentiment_score"], reverse=True)

        # Generate suggested priorities
        priorities = []

        # Add pain points to priorities (most critical first)
        if pain_points:
            priorities.append(f"Address critical issue: {pain_points[0]['text'][:100]}...")

            # Add more pain points if available
            if len(pain_points) > 1:
                priorities.append(f"Fix secondary issue: {pain_points[1]['text'][:100]}...")

        # Add feature requests to priorities
        if feature_requests:
            priorities.append(f"Implement requested feature: {feature_requests[0]['text'][:100]}...")

        # Add general recommendation
        if positive_feedback:
            priorities.append(f"Maintain strengths: {positive_feedback[0]['text'][:100]}...")

        # Get top 3 of each category (or fewer if not available)
        top_pain_points = pain_points[:3]
        top_feature_requests = feature_requests[:3]
        top_positive_feedback = positive_feedback[:3]

        # Create summary items with required fields
        pain_point_items = [
            {
                "text": item["text"],
                "sentiment_score": item["sentiment_score"],
                "keywords": item["keywords"]
            } for item in top_pain_points
        ]

        feature_request_items = [
            {
                "text": item["text"],
                "sentiment_score": item["sentiment_score"],
                "keywords": item["keywords"]
            } for item in top_feature_requests
        ]

        positive_feedback_items = [
            {
                "text": item["text"],
                "sentiment_score": item["sentiment_score"],
                "keywords": item["keywords"]
            } for item in top_positive_feedback
        ]

        return {
            "pain_points": pain_point_items,
            "feature_requests": feature_request_items,
            "positive_feedback": positive_feedback_items,
            "suggested_priorities": priorities
        }