import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
import re
from collections import Counter
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

class LargeCSVProcessor:
    def __init__(self):
        """Initialize the CSV processor with NLTK components"""
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Keywords for classification
        self.pain_point_keywords = {
            'error', 'bug', 'crash', 'issue', 'problem', 'broken', 'fail',
            'slow', 'lag', 'freeze', 'glitch', 'not working', 'doesn\'t work'
        }
        self.feature_request_keywords = {
            'add', 'implement', 'feature', 'request', 'suggestion', 'would like',
            'should have', 'need', 'want', 'missing', 'could you'
        }

    def process_csv_in_chunks(self, file_path: str, chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Process a large CSV file in chunks and perform local analysis
        
        Args:
            file_path: Path to the CSV file
            chunk_size: Number of rows to process at once
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting to process CSV file: {file_path}")
        
        # Initialize results storage
        all_reviews = []
        sentiment_scores = []
        classifications = []
        keywords = []
        
        # Process the CSV in chunks
        for chunk in pd.read_csv(file_path, header=None, names=['id', 'game', 'sentiment', 'text'], chunksize=chunk_size):
            logger.info(f"Processing chunk of {len(chunk)} rows")
            
            # Process each row in the chunk
            for _, row in chunk.iterrows():
                if pd.isna(row['text']) or str(row['text']).strip() == '':
                    continue
                    
                text = str(row['text'])
                
                # Perform sentiment analysis
                sentiment = self.sentiment_analyzer.polarity_scores(text)
                sentiment_scores.append(sentiment['compound'])
                
                # Classify feedback
                classification = self.classify_feedback(text)
                classifications.append(classification)
                
                # Extract keywords
                text_keywords = self.extract_keywords(text)
                keywords.extend(text_keywords)
                
                # Store review data
                review_data = {
                    'text': text,
                    'game': str(row['game']) if not pd.isna(row['game']) else None,
                    'sentiment': str(row['sentiment']) if not pd.isna(row['sentiment']) else None,
                    'sentiment_score': sentiment['compound'],
                    'sentiment_label': self.get_sentiment_label(sentiment['compound']),
                    'classification': classification,
                    'keywords': text_keywords
                }
                all_reviews.append(review_data)
        
        # Generate summary statistics
        summary = self.generate_summary(all_reviews, sentiment_scores, classifications, keywords)
        
        return {
            'reviews': all_reviews,
            'summary': summary
        }

    def clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_keywords(self, text: str, n_keywords: int = 5) -> List[str]:
        """Extract keywords from text"""
        text = self.clean_text(text)
        tokens = word_tokenize(text)
        filtered_tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2]
        lemmatized_tokens = [self.lemmatizer.lemmatize(word) for word in filtered_tokens]
        word_counts = Counter(lemmatized_tokens)
        return [word for word, _ in word_counts.most_common(n_keywords)]

    def classify_feedback(self, text: str) -> str:
        """Classify feedback into categories"""
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in self.pain_point_keywords):
            return "pain_point"
        if any(keyword in text_lower for keyword in self.feature_request_keywords):
            return "feature_request"
        return "positive_feedback"

    def get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.05:
            return "POSITIVE"
        elif score <= -0.05:
            return "NEGATIVE"
        return "NEUTRAL"

    def generate_summary(self, reviews: List[Dict], sentiment_scores: List[float],
                        classifications: List[str], keywords: List[str]) -> Dict[str, Any]:
        """Generate summary statistics from the analysis"""
        # Calculate sentiment statistics
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        sentiment_distribution = {
            'positive': sum(1 for s in sentiment_scores if s >= 0.05),
            'neutral': sum(1 for s in sentiment_scores if -0.05 < s < 0.05),
            'negative': sum(1 for s in sentiment_scores if s <= -0.05)
        }
        
        # Calculate classification distribution
        classification_distribution = Counter(classifications)
        
        # Get top keywords
        keyword_distribution = Counter(keywords).most_common(20)
        
        # Calculate game distribution
        game_distribution = Counter(r['game'] for r in reviews if r['game'] is not None)
        
        return {
            'total_reviews': len(reviews),
            'average_sentiment': avg_sentiment,
            'sentiment_distribution': sentiment_distribution,
            'classification_distribution': dict(classification_distribution),
            'top_keywords': dict(keyword_distribution),
            'game_distribution': dict(game_distribution),
            'timestamp': datetime.now().isoformat()
        }

    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save analysis results to a JSON file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}") 