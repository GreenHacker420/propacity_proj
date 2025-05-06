import google.generativeai as genai
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class TextClassifier:
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    async def classify_feedback(self, text: str) -> str:
        """
        Classify the feedback into one of the following categories:
        - pain_point: User is reporting an issue or problem
        - feature_request: User is requesting a new feature
        - positive_feedback: User is providing positive feedback
        """
        prompt = f"""
        Classify the following feedback into exactly one of these categories:
        - pain_point: User is reporting an issue or problem
        - feature_request: User is requesting a new feature
        - positive_feedback: User is providing positive feedback

        Only return the category name, nothing else.

        Feedback: {text}
        """

        try:
            response = await self.model.generate_content(prompt)
            category = response.text.strip().lower()
            
            # Validate category
            valid_categories = ["pain_point", "feature_request", "positive_feedback"]
            if category not in valid_categories:
                return "positive_feedback"  # Default to positive feedback if classification fails
                
            return category
        except Exception as e:
            print(f"Error classifying feedback: {str(e)}")
            return "positive_feedback"  # Default to positive feedback on error

    async def extract_keywords(self, text: str) -> List[str]:
        """
        Extract key phrases or words from the text that are relevant to the feedback.
        """
        prompt = f"""
        Extract the most important keywords or phrases from the following text.
        Return them as a comma-separated list, with no additional text.
        Focus on terms that indicate the main topic, issue, or feature being discussed.

        Text: {text}
        """

        try:
            response = await self.model.generate_content(prompt)
            keywords = [k.strip() for k in response.text.strip().split(",")]
            return keywords
        except Exception as e:
            print(f"Error extracting keywords: {str(e)}")
            return []

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
            response = await self.model.generate_content(prompt)
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
        return [await self.classify_feedback(text) for text in texts]

    async def extract_keywords_batch(self, texts: List[str]) -> List[List[str]]:
        """
        Extract keywords from a batch of texts.
        Returns a list of keyword lists.
        """
        return [await self.extract_keywords(text) for text in texts] 