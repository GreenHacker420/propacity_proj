import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import matplotlib.pyplot as plt
import io
import base64
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import re

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

class TopicModeler:
    """
    Class for performing topic modeling on text data
    """
    
    def __init__(self):
        """
        Initialize the topic modeler
        """
        logger.info("Initializing Topic Modeler...")
        self.stop_words = set(stopwords.words('english'))
        
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for topic modeling
        
        Args:
            text: The text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and short words
        filtered_tokens = [word for word in tokens if word not in self.stop_words and len(word) > 2]
        
        # Join tokens back into a string
        return ' '.join(filtered_tokens)
    
    def extract_topics(self, texts: List[str], n_topics: int = 5, n_top_words: int = 10) -> Dict[str, Any]:
        """
        Extract topics from a list of texts
        
        Args:
            texts: List of texts to analyze
            n_topics: Number of topics to extract
            n_top_words: Number of top words to include per topic
            
        Returns:
            Dictionary containing topics and their visualization
        """
        if not texts:
            return {"topics": [], "topic_distribution": None}
            
        try:
            # Preprocess texts
            preprocessed_texts = [self.preprocess_text(text) for text in texts if text]
            
            if not preprocessed_texts:
                return {"topics": [], "topic_distribution": None}
            
            # Create document-term matrix
            vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=1000)
            dtm = vectorizer.fit_transform(preprocessed_texts)
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Fit LDA model
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                learning_method='online',
                max_iter=10
            )
            
            lda.fit(dtm)
            
            # Extract topics
            topics = []
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[:-n_top_words - 1:-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topics.append({
                    "id": topic_idx,
                    "words": top_words,
                    "weight": float(topic.sum() / lda.components_.sum())
                })
            
            # Generate topic distribution visualization
            topic_distribution = self._generate_topic_distribution_chart(topics)
            
            return {
                "topics": topics,
                "topic_distribution": topic_distribution
            }
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return {"topics": [], "topic_distribution": None}
    
    def _generate_topic_distribution_chart(self, topics: List[Dict[str, Any]]) -> str:
        """
        Generate a visualization of topic distribution
        
        Args:
            topics: List of topic dictionaries
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Extract topic weights and labels
            weights = [topic["weight"] for topic in topics]
            labels = [f"Topic {topic['id']+1}" for topic in topics]
            
            # Create pie chart
            plt.pie(
                weights, 
                labels=labels, 
                autopct='%1.1f%%',
                startangle=90,
                shadow=True
            )
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Topic Distribution', fontsize=16)
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating topic distribution chart: {str(e)}")
            return ""
