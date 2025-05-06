import logging
from typing import List, Dict, Any, Optional
from transformers import pipeline
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionDetector:
    """
    Class for detecting emotions in text
    """
    
    def __init__(self):
        """
        Initialize the emotion detector
        """
        logger.info("Initializing Emotion Detector...")
        try:
            # Load emotion detection model
            self.emotion_model = pipeline(
                "text-classification", 
                model="j-hartmann/emotion-english-distilroberta-base", 
                top_k=None
            )
            logger.info("Emotion detection model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading emotion detection model: {str(e)}")
            self.emotion_model = None
            logger.warning("Using fallback emotion detection")
    
    def detect_emotion(self, text: str) -> Dict[str, float]:
        """
        Detect emotions in text
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary mapping emotion labels to scores
        """
        if not self.emotion_model or not text:
            return self._fallback_emotion_detection(text)
            
        try:
            # Get emotion predictions
            results = self.emotion_model(text[:512])  # Limit text length for model
            
            # Extract scores for each emotion
            emotions = {}
            for result in results[0]:
                emotions[result['label']] = result['score']
            
            return emotions
        except Exception as e:
            logger.error(f"Error detecting emotions: {str(e)}")
            return self._fallback_emotion_detection(text)
    
    def _fallback_emotion_detection(self, text: str) -> Dict[str, float]:
        """
        Fallback emotion detection based on keyword matching
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary mapping emotion labels to scores
        """
        text = text.lower()
        
        # Define emotion keywords
        emotion_keywords = {
            'joy': ['happy', 'joy', 'delighted', 'pleased', 'glad', 'excited', 'love'],
            'sadness': ['sad', 'unhappy', 'disappointed', 'depressed', 'upset', 'miserable'],
            'anger': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'frustrated'],
            'fear': ['afraid', 'scared', 'frightened', 'terrified', 'worried', 'anxious'],
            'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'unexpected'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'gross', 'yuck'],
            'neutral': ['ok', 'okay', 'fine', 'normal', 'average', 'neutral']
        }
        
        # Count emotion keywords
        emotion_counts = {emotion: 0 for emotion in emotion_keywords}
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_counts[emotion] += 1
        
        # Calculate scores
        total_count = sum(emotion_counts.values()) or 1  # Avoid division by zero
        emotion_scores = {emotion: count / total_count for emotion, count in emotion_counts.items()}
        
        # If no emotions detected, set neutral to 1.0
        if all(score == 0 for score in emotion_scores.values()):
            emotion_scores['neutral'] = 1.0
        
        return emotion_scores
    
    def analyze_emotions(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze emotions across multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary containing emotion analysis results
        """
        if not texts:
            return {"emotions": {}, "visualization": None}
            
        try:
            # Detect emotions in all texts
            all_emotions = []
            for text in texts:
                if not text:
                    continue
                    
                emotions = self.detect_emotion(text)
                all_emotions.append(emotions)
            
            if not all_emotions:
                return {"emotions": {}, "visualization": None}
            
            # Aggregate emotions
            emotion_totals = Counter()
            for emotions in all_emotions:
                # Get the dominant emotion
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                emotion_totals[dominant_emotion] += 1
            
            # Calculate percentages
            total_count = sum(emotion_totals.values())
            emotion_percentages = {
                emotion: count / total_count
                for emotion, count in emotion_totals.items()
            }
            
            # Generate visualization
            visualization = self._generate_emotion_chart(emotion_totals)
            
            return {
                "emotions": dict(emotion_totals),
                "percentages": emotion_percentages,
                "visualization": visualization
            }
        except Exception as e:
            logger.error(f"Error analyzing emotions: {str(e)}")
            return {"emotions": {}, "visualization": None}
    
    def _generate_emotion_chart(self, emotion_counts: Dict[str, int]) -> str:
        """
        Generate a visualization of emotion distribution
        
        Args:
            emotion_counts: Dictionary mapping emotions to counts
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not emotion_counts:
                return ""
                
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Define colors for emotions
            emotion_colors = {
                'joy': '#FFD700',      # Gold
                'sadness': '#4682B4',  # Steel Blue
                'anger': '#FF4500',    # Orange Red
                'fear': '#800080',     # Purple
                'surprise': '#32CD32', # Lime Green
                'disgust': '#8B4513',  # Saddle Brown
                'neutral': '#A9A9A9'   # Dark Gray
            }
            
            # Extract data
            emotions = list(emotion_counts.keys())
            counts = list(emotion_counts.values())
            
            # Get colors for each emotion
            colors = [emotion_colors.get(emotion, '#A9A9A9') for emotion in emotions]
            
            # Create pie chart
            plt.pie(
                counts, 
                labels=emotions, 
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                shadow=True
            )
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Emotion Distribution', fontsize=16)
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating emotion chart: {str(e)}")
            return ""
