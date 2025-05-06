import matplotlib.pyplot as plt
import matplotlib
import io
import base64
import numpy as np
from typing import List, Dict, Any, Optional
import tempfile
import os
from datetime import datetime, timedelta
import logging

# Configure matplotlib to use Agg backend (non-interactive, good for web servers)
matplotlib.use('Agg')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Visualizer:
    """
    Class for generating visualizations from review data
    """
    
    @staticmethod
    def generate_sentiment_chart(reviews: List[Dict[str, Any]]) -> str:
        """
        Generate a sentiment distribution chart
        
        Args:
            reviews: List of review dictionaries with sentiment data
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Count sentiments
            sentiments = {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0}
            for review in reviews:
                label = review.get('sentiment_label', 'NEUTRAL')
                if label in sentiments:
                    sentiments[label] += 1
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Create bar chart
            labels = list(sentiments.keys())
            values = list(sentiments.values())
            colors = ['#4CAF50', '#FFC107', '#F44336']  # Green, Yellow, Red
            
            plt.bar(labels, values, color=colors)
            plt.title('Sentiment Distribution', fontsize=16)
            plt.ylabel('Number of Reviews', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add values on top of bars
            for i, v in enumerate(values):
                plt.text(i, v + 0.5, str(v), ha='center', fontweight='bold')
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating sentiment chart: {str(e)}")
            return ""
    
    @staticmethod
    def generate_rating_chart(reviews: List[Dict[str, Any]]) -> str:
        """
        Generate a rating distribution chart
        
        Args:
            reviews: List of review dictionaries with rating data
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Extract ratings
            ratings = [review.get('rating') for review in reviews if review.get('rating') is not None]
            
            if not ratings:
                return ""
            
            # Count ratings
            rating_counts = {}
            for rating in range(1, 6):
                rating_counts[rating] = ratings.count(rating)
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Create bar chart
            labels = list(rating_counts.keys())
            values = list(rating_counts.values())
            
            # Color gradient from red to green
            colors = ['#F44336', '#FF9800', '#FFC107', '#8BC34A', '#4CAF50']
            
            plt.bar(labels, values, color=colors)
            plt.title('Rating Distribution', fontsize=16)
            plt.xlabel('Rating', fontsize=12)
            plt.ylabel('Number of Reviews', fontsize=12)
            plt.xticks(labels)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Add values on top of bars
            for i, v in enumerate(values):
                plt.text(i + 1, v + 0.5, str(v), ha='center', fontweight='bold')
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating rating chart: {str(e)}")
            return ""
    
    @staticmethod
    def generate_keyword_chart(reviews: List[Dict[str, Any]], top_n: int = 10) -> str:
        """
        Generate a chart of the most common keywords
        
        Args:
            reviews: List of review dictionaries with keywords
            top_n: Number of top keywords to show
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Extract all keywords
            all_keywords = []
            for review in reviews:
                keywords = review.get('keywords', [])
                all_keywords.extend(keywords)
            
            if not all_keywords:
                return ""
            
            # Count keywords
            keyword_counts = {}
            for keyword in all_keywords:
                if keyword in keyword_counts:
                    keyword_counts[keyword] += 1
                else:
                    keyword_counts[keyword] = 1
            
            # Get top N keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create horizontal bar chart
            labels = [kw[0] for kw in top_keywords]
            values = [kw[1] for kw in top_keywords]
            
            # Reverse order for better visualization
            labels.reverse()
            values.reverse()
            
            plt.barh(labels, values, color='#2196F3')
            plt.title('Top Keywords', fontsize=16)
            plt.xlabel('Frequency', fontsize=12)
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Add values at the end of bars
            for i, v in enumerate(values):
                plt.text(v + 0.1, i, str(v), va='center', fontweight='bold')
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating keyword chart: {str(e)}")
            return ""
