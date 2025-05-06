import google.generativeai as genai
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    async def analyze_sentiment(self, text: str) -> float:
        """
        Analyze the sentiment of the given text using Gemini API.
        Returns a score between -1 (very negative) and 1 (very positive).
        """
        prompt = f"""
        Analyze the sentiment of the following text and provide a score between -1 and 1,
        where -1 is very negative and 1 is very positive. Only return the numerical score.

        Text: {text}
        """

        try:
            response = await self.model.generate_content(prompt)
            score = float(response.text.strip())
            return max(min(score, 1.0), -1.0)  # Ensure score is between -1 and 1
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return 0.0  # Return neutral sentiment on error

    async def analyze_sentiment_batch(self, texts: list[str]) -> list[float]:
        """
        Analyze sentiment for a batch of texts.
        Returns a list of scores between -1 and 1.
        """
        return [await self.analyze_sentiment(text) for text in texts]

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
            response = await self.model.generate_content(prompt)
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