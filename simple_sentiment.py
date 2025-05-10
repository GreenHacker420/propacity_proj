"""
Simple sentiment analyzer that works reliably without dependencies on spaCy or other complex models.
This is a fallback implementation that will work even when other models fail.
"""

import logging
import time
import concurrent.futures
import os
from typing import List, Dict, Any
import re
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSentimentAnalyzer:
    """
    A simple sentiment analyzer that uses basic rules and patterns to analyze sentiment.
    This is a fallback implementation that will work even when other models fail.
    """
    
    def __init__(self):
        """Initialize the simple sentiment analyzer"""
        logger.info("Initializing Simple Sentiment Analyzer")
        
        # Load positive and negative word lists
        self.positive_words = self._load_word_list('positive')
        self.negative_words = self._load_word_list('negative')
        
        # Initialize sentiment cache
        self.sentiment_cache = {}
        
    def _load_word_list(self, sentiment_type):
        """Load a list of words with the given sentiment"""
        if sentiment_type == 'positive':
            return {
                'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'wonderful',
                'love', 'best', 'perfect', 'nice', 'happy', 'helpful', 'easy', 'recommend',
                'like', 'enjoy', 'pleased', 'satisfied', 'impressive', 'beautiful', 'fast',
                'reliable', 'efficient', 'convenient', 'friendly', 'useful', 'worth', 'favorite',
                'simple', 'smooth', 'intuitive', 'innovative', 'responsive', 'quick', 'fun',
                'effective', 'quality', 'valuable', 'positive', 'outstanding', 'superb', 'superior'
            }
        else:
            return {
                'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate', 'difficult',
                'slow', 'expensive', 'disappointing', 'useless', 'annoying', 'frustrating',
                'broken', 'issue', 'problem', 'bug', 'error', 'crash', 'fail', 'failure',
                'waste', 'confusing', 'complicated', 'hard', 'impossible', 'negative', 'ugly',
                'unreliable', 'inconsistent', 'inconvenient', 'unhelpful', 'unfriendly',
                'inefficient', 'ineffective', 'overpriced', 'expensive', 'cheap', 'glitchy',
                'laggy', 'buggy', 'unstable', 'unusable', 'disappointing', 'mediocre'
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of a single text
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text or not text.strip():
            return {
                "sentiment_score": 0.5,
                "sentiment_label": "NEUTRAL",
                "confidence": 0.0,
                "is_sarcastic": False,
                "sarcasm_confidence": 0.0,
                "context_analysis": {},
                "aspect_sentiments": []
            }
            
        # Check cache
        if text in self.sentiment_cache:
            return self.sentiment_cache[text]
            
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Count positive and negative words
        positive_count = sum(1 for word in cleaned_text.split() if word.lower() in self.positive_words)
        negative_count = sum(1 for word in cleaned_text.split() if word.lower() in self.negative_words)
        
        # Calculate sentiment score (0 to 1)
        total_count = positive_count + negative_count
        if total_count == 0:
            sentiment_score = 0.5  # Neutral
            confidence = 0.0
        else:
            sentiment_score = positive_count / total_count
            confidence = min(1.0, total_count / 10)  # More words = higher confidence, max 1.0
        
        # Determine sentiment label
        if sentiment_score > 0.6:
            sentiment_label = "POSITIVE"
        elif sentiment_score < 0.4:
            sentiment_label = "NEGATIVE"
        else:
            sentiment_label = "NEUTRAL"
            
        # Create result
        result = {
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "confidence": confidence,
            "is_sarcastic": False,
            "sarcasm_confidence": 0.0,
            "context_analysis": {},
            "aspect_sentiments": []
        }
        
        # Cache result
        self.sentiment_cache[text] = result
        
        return result
    
    def analyze_sentiment_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for a batch of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of dictionaries with sentiment analysis results
        """
        logger.info(f"Processing batch of {len(texts)} texts with simple sentiment analyzer")
        start_time = time.time()
        
        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 2)) as executor:
            results = list(executor.map(self.analyze_sentiment, texts))
            
        processing_time = time.time() - start_time
        logger.info(f"Batch sentiment analysis completed in {processing_time:.2f} seconds")
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Create a singleton instance
simple_sentiment_analyzer = SimpleSentimentAnalyzer()
