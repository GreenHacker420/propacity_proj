import logging
from typing import List, Dict, Any, Optional
import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import defaultdict
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

class AspectSentimentAnalyzer:
    """
    Class for performing aspect-based sentiment analysis
    """
    
    def __init__(self):
        """
        Initialize the aspect-based sentiment analyzer
        """
        logger.info("Initializing Aspect-Based Sentiment Analyzer...")
        try:
            # Load spaCy model for dependency parsing
            self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize VADER sentiment analyzer
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            
            logger.info("Aspect-Based Sentiment Analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Aspect-Based Sentiment Analyzer: {str(e)}")
            self.nlp = None
            self.sentiment_analyzer = None
    
    def extract_aspects(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract aspects and their sentiment from text
        
        Args:
            text: The text to analyze
            
        Returns:
            List of dictionaries containing aspect and sentiment
        """
        if not self.nlp or not text:
            return []
            
        try:
            # Process the text with spaCy
            doc = self.nlp(text)
            
            aspects = []
            
            # Extract noun phrases as potential aspects
            for chunk in doc.noun_chunks:
                # Get the root of the noun phrase
                root = chunk.root
                
                # Extract the aspect
                aspect = root.text.lower()
                
                # Get the surrounding context (5 words before and after)
                start_idx = max(0, root.i - 5)
                end_idx = min(len(doc), root.i + 6)
                context = doc[start_idx:end_idx].text
                
                # Calculate sentiment for the context
                sentiment_scores = self.sentiment_analyzer.polarity_scores(context)
                
                # Determine sentiment label
                if sentiment_scores['compound'] >= 0.05:
                    sentiment_label = "POSITIVE"
                elif sentiment_scores['compound'] <= -0.05:
                    sentiment_label = "NEGATIVE"
                else:
                    sentiment_label = "NEUTRAL"
                
                aspects.append({
                    "aspect": aspect,
                    "context": context,
                    "sentiment_score": sentiment_scores['compound'],
                    "sentiment_label": sentiment_label
                })
            
            return aspects
        except Exception as e:
            logger.error(f"Error extracting aspects: {str(e)}")
            return []
    
    def analyze_aspects(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze aspects across multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary containing aspect analysis results
        """
        if not self.nlp or not texts:
            return {"aspects": {}, "visualization": None}
            
        try:
            # Extract aspects from all texts
            all_aspects = []
            for text in texts:
                if not text:
                    continue
                    
                aspects = self.extract_aspects(text)
                all_aspects.extend(aspects)
            
            # Group aspects by name
            aspect_groups = defaultdict(list)
            for aspect_data in all_aspects:
                aspect_groups[aspect_data["aspect"]].append(aspect_data)
            
            # Calculate average sentiment for each aspect
            aspect_sentiments = {}
            for aspect, data_list in aspect_groups.items():
                # Skip aspects that appear only once
                if len(data_list) < 2:
                    continue
                    
                # Calculate average sentiment score
                avg_sentiment = sum(data["sentiment_score"] for data in data_list) / len(data_list)
                
                # Count sentiment labels
                sentiment_counts = {
                    "POSITIVE": sum(1 for data in data_list if data["sentiment_label"] == "POSITIVE"),
                    "NEUTRAL": sum(1 for data in data_list if data["sentiment_label"] == "NEUTRAL"),
                    "NEGATIVE": sum(1 for data in data_list if data["sentiment_label"] == "NEGATIVE")
                }
                
                # Determine overall sentiment label
                if sentiment_counts["POSITIVE"] > sentiment_counts["NEGATIVE"]:
                    overall_label = "POSITIVE"
                elif sentiment_counts["NEGATIVE"] > sentiment_counts["POSITIVE"]:
                    overall_label = "NEGATIVE"
                else:
                    overall_label = "NEUTRAL"
                
                aspect_sentiments[aspect] = {
                    "count": len(data_list),
                    "avg_sentiment": avg_sentiment,
                    "sentiment_label": overall_label,
                    "sentiment_counts": sentiment_counts
                }
            
            # Sort aspects by count (most mentioned first)
            sorted_aspects = dict(sorted(
                aspect_sentiments.items(), 
                key=lambda item: item[1]["count"], 
                reverse=True
            )[:10])  # Limit to top 10 aspects
            
            # Generate visualization
            visualization = self._generate_aspect_sentiment_chart(sorted_aspects)
            
            return {
                "aspects": sorted_aspects,
                "visualization": visualization
            }
        except Exception as e:
            logger.error(f"Error analyzing aspects: {str(e)}")
            return {"aspects": {}, "visualization": None}
    
    def _generate_aspect_sentiment_chart(self, aspect_sentiments: Dict[str, Dict[str, Any]]) -> str:
        """
        Generate a visualization of aspect sentiments
        
        Args:
            aspect_sentiments: Dictionary mapping aspects to sentiment data
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not aspect_sentiments:
                return ""
                
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Extract data
            aspects = list(aspect_sentiments.keys())
            counts = [data["count"] for data in aspect_sentiments.values()]
            sentiments = [data["avg_sentiment"] for data in aspect_sentiments.values()]
            
            # Create color map based on sentiment
            colors = ['#F44336' if s < -0.05 else '#4CAF50' if s > 0.05 else '#FFC107' for s in sentiments]
            
            # Create horizontal bar chart
            y_pos = np.arange(len(aspects))
            plt.barh(y_pos, counts, color=colors)
            plt.yticks(y_pos, aspects)
            
            # Add sentiment labels
            for i, (count, sentiment) in enumerate(zip(counts, sentiments)):
                sentiment_label = f"{sentiment:.2f}"
                plt.text(count + 0.1, i, sentiment_label, va='center')
            
            plt.xlabel('Mention Count')
            plt.title('Aspect Sentiment Analysis')
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#4CAF50', label='Positive'),
                Patch(facecolor='#FFC107', label='Neutral'),
                Patch(facecolor='#F44336', label='Negative')
            ]
            plt.legend(handles=legend_elements, loc='lower right')
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating aspect sentiment chart: {str(e)}")
            return ""
