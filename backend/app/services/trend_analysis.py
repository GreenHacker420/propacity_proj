import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """
    Class for analyzing trends in review data over time
    """
    
    def __init__(self):
        """
        Initialize the trend analyzer
        """
        logger.info("Initializing Trend Analyzer...")
    
    def analyze_trends(self, reviews: List[Dict[str, Any]], time_period: str = 'month') -> Dict[str, Any]:
        """
        Analyze trends in review data over time
        
        Args:
            reviews: List of review dictionaries
            time_period: Time period for grouping ('day', 'week', 'month')
            
        Returns:
            Dictionary containing trend analysis results
        """
        if not reviews:
            return {
                "sentiment_trend": None,
                "rating_trend": None,
                "volume_trend": None
            }
            
        try:
            # Convert reviews to DataFrame
            df = pd.DataFrame(reviews)
            
            # Ensure timestamp column exists and is datetime
            if 'timestamp' not in df.columns:
                return {
                    "sentiment_trend": None,
                    "rating_trend": None,
                    "volume_trend": None
                }
            
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Drop rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
            
            if df.empty:
                return {
                    "sentiment_trend": None,
                    "rating_trend": None,
                    "volume_trend": None
                }
            
            # Determine time grouping
            if time_period == 'day':
                df['time_group'] = df['timestamp'].dt.date
            elif time_period == 'week':
                df['time_group'] = df['timestamp'].dt.to_period('W').dt.start_time
            else:  # Default to month
                df['time_group'] = df['timestamp'].dt.to_period('M').dt.start_time
            
            # Group by time period
            grouped = df.groupby('time_group')
            
            # Calculate metrics for each time period
            time_metrics = []
            for time_group, group in grouped:
                metrics = {
                    'time_period': time_group,
                    'review_count': len(group),
                    'avg_sentiment': group['sentiment_score'].mean() if 'sentiment_score' in group else None,
                    'avg_rating': group['rating'].mean() if 'rating' in group else None,
                    'positive_count': sum(1 for s in group['sentiment_label'] if s == 'POSITIVE') if 'sentiment_label' in group else 0,
                    'neutral_count': sum(1 for s in group['sentiment_label'] if s == 'NEUTRAL') if 'sentiment_label' in group else 0,
                    'negative_count': sum(1 for s in group['sentiment_label'] if s == 'NEGATIVE') if 'sentiment_label' in group else 0
                }
                time_metrics.append(metrics)
            
            # Sort by time period
            time_metrics.sort(key=lambda x: x['time_period'])
            
            # Generate visualizations
            sentiment_trend = self._generate_sentiment_trend_chart(time_metrics)
            rating_trend = self._generate_rating_trend_chart(time_metrics)
            volume_trend = self._generate_volume_trend_chart(time_metrics)
            
            return {
                "time_metrics": time_metrics,
                "sentiment_trend": sentiment_trend,
                "rating_trend": rating_trend,
                "volume_trend": volume_trend
            }
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {
                "sentiment_trend": None,
                "rating_trend": None,
                "volume_trend": None
            }
    
    def _generate_sentiment_trend_chart(self, time_metrics: List[Dict[str, Any]]) -> str:
        """
        Generate a visualization of sentiment trends over time
        
        Args:
            time_metrics: List of time period metrics
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not time_metrics:
                return ""
                
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Extract data
            time_periods = [m['time_period'] for m in time_metrics]
            avg_sentiments = [m['avg_sentiment'] for m in time_metrics]
            
            # Create line chart
            plt.plot(time_periods, avg_sentiments, marker='o', linestyle='-', color='#2196F3')
            
            # Add horizontal line at 0.5 (neutral sentiment)
            plt.axhline(y=0.5, color='#757575', linestyle='--', alpha=0.7)
            
            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gcf().autofmt_xdate()
            
            plt.title('Sentiment Trend Over Time', fontsize=16)
            plt.ylabel('Average Sentiment Score', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Set y-axis limits
            plt.ylim(0, 1)
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating sentiment trend chart: {str(e)}")
            return ""
    
    def _generate_rating_trend_chart(self, time_metrics: List[Dict[str, Any]]) -> str:
        """
        Generate a visualization of rating trends over time
        
        Args:
            time_metrics: List of time period metrics
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not time_metrics or all(m['avg_rating'] is None for m in time_metrics):
                return ""
                
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Extract data
            time_periods = [m['time_period'] for m in time_metrics]
            avg_ratings = [m['avg_rating'] for m in time_metrics]
            
            # Create line chart
            plt.plot(time_periods, avg_ratings, marker='o', linestyle='-', color='#FF9800')
            
            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gcf().autofmt_xdate()
            
            plt.title('Rating Trend Over Time', fontsize=16)
            plt.ylabel('Average Rating', fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Set y-axis limits
            plt.ylim(0, 5.5)
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating rating trend chart: {str(e)}")
            return ""
    
    def _generate_volume_trend_chart(self, time_metrics: List[Dict[str, Any]]) -> str:
        """
        Generate a visualization of review volume trends over time
        
        Args:
            time_metrics: List of time period metrics
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            if not time_metrics:
                return ""
                
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Extract data
            time_periods = [m['time_period'] for m in time_metrics]
            review_counts = [m['review_count'] for m in time_metrics]
            positive_counts = [m['positive_count'] for m in time_metrics]
            neutral_counts = [m['neutral_count'] for m in time_metrics]
            negative_counts = [m['negative_count'] for m in time_metrics]
            
            # Create stacked bar chart
            plt.bar(time_periods, positive_counts, label='Positive', color='#4CAF50')
            plt.bar(time_periods, neutral_counts, bottom=positive_counts, label='Neutral', color='#FFC107')
            plt.bar(time_periods, negative_counts, bottom=[p+n for p,n in zip(positive_counts, neutral_counts)], label='Negative', color='#F44336')
            
            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gcf().autofmt_xdate()
            
            plt.title('Review Volume Over Time', fontsize=16)
            plt.ylabel('Number of Reviews', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating volume trend chart: {str(e)}")
            return ""
