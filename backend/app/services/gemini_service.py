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
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self.available = GEMINI_AVAILABLE and self.api_key is not None
        
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
            self.models = [m.name for m in genai.list_models() if 'gemini' in m.name]
            
            if not self.models:
                logger.warning("No Gemini models available")
                self.available = False
                return
                
            # Check if specified model is available
            if self.model_name not in self.models:
                logger.warning(f"Specified model {self.model_name} not available. Using {self.models[0]} instead.")
                self.model_name = self.models[0]
                
            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Gemini API: {str(e)}")
            self.available = False
    
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
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.replace("```json", "", 1)
                if text.endswith("```"):
                    text = text.rsplit("```", 1)[0]
                text = text.strip()
                result = json.loads(text)
            
            processing_time = time.time() - start_time
            logger.info(f"Gemini sentiment analysis completed in {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini sentiment analysis: {str(e)}")
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
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Gemini batch review analysis: {str(e)}")
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
                "key_points": [],
                "pain_points": [],
                "feature_requests": [],
                "positive_aspects": []
            }
            
        try:
            start_time = time.time()
            
            # Prepare the prompt with all reviews
            reviews_text = "\n".join([f"Review {i+1}: {review}" for i, review in enumerate(reviews)])
            
            prompt = f"""
            Analyze the following product reviews and extract insights. Return a JSON object with:
            - summary: A brief summary of the overall feedback
            - key_points: Array of the most important points mentioned across reviews
            - pain_points: Array of issues or problems mentioned by users
            - feature_requests: Array of features or improvements requested by users
            - positive_aspects: Array of positive aspects mentioned by users
            
            Reviews:
            {reviews_text}
            
            Return only the JSON object without any additional text.
            """
            
            response = self.model.generate_content(prompt)
            
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
                result = json.loads(text)
            
            processing_time = time.time() - start_time
            logger.info(f"Gemini insight extraction completed in {processing_time:.2f} seconds for {len(reviews)} reviews")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini insight extraction: {str(e)}")
            return {
                "summary": f"Error extracting insights: {str(e)}",
                "key_points": [],
                "pain_points": [],
                "feature_requests": [],
                "positive_aspects": []
            }
