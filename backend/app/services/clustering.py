import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
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

class FeedbackClusterer:
    """
    Class for clustering user feedback
    """
    
    def __init__(self):
        """
        Initialize the feedback clusterer
        """
        logger.info("Initializing Feedback Clusterer...")
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for clustering
        
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
    
    def cluster_feedback(self, reviews: List[Dict[str, Any]], n_clusters: int = 5) -> Dict[str, Any]:
        """
        Cluster reviews based on text content
        
        Args:
            reviews: List of review dictionaries
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary containing clustering results
        """
        if not reviews:
            return {
                "clusters": [],
                "visualization": None
            }
            
        try:
            # Extract and preprocess text
            texts = [review.get('text', '') for review in reviews]
            preprocessed_texts = [self.preprocess_text(text) for text in texts if text]
            
            if not preprocessed_texts:
                return {
                    "clusters": [],
                    "visualization": None
                }
            
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(preprocessed_texts)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(preprocessed_texts)), random_state=42)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Get cluster centers
            cluster_centers = kmeans.cluster_centers_
            
            # Extract top keywords for each cluster
            clusters = []
            for i in range(len(cluster_centers)):
                # Get indices of top terms for this cluster
                top_indices = cluster_centers[i].argsort()[-10:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                
                # Get reviews in this cluster
                cluster_reviews = [
                    reviews[j] for j in range(len(reviews)) 
                    if j < len(cluster_labels) and cluster_labels[j] == i
                ]
                
                # Calculate average sentiment for this cluster
                avg_sentiment = sum(
                    review.get('sentiment_score', 0.5) for review in cluster_reviews
                ) / len(cluster_reviews) if cluster_reviews else 0.5
                
                # Count sentiment labels
                sentiment_counts = Counter(
                    review.get('sentiment_label', 'NEUTRAL') for review in cluster_reviews
                )
                
                # Determine dominant sentiment
                dominant_sentiment = sentiment_counts.most_common(1)[0][0] if sentiment_counts else 'NEUTRAL'
                
                clusters.append({
                    "id": i,
                    "size": len(cluster_reviews),
                    "top_terms": top_terms,
                    "avg_sentiment": avg_sentiment,
                    "dominant_sentiment": dominant_sentiment,
                    "sample_reviews": [review.get('text', '') for review in cluster_reviews[:3]]
                })
            
            # Sort clusters by size (largest first)
            clusters.sort(key=lambda x: x["size"], reverse=True)
            
            # Generate visualization
            visualization = self._generate_cluster_visualization(tfidf_matrix, cluster_labels, clusters)
            
            return {
                "clusters": clusters,
                "visualization": visualization
            }
        except Exception as e:
            logger.error(f"Error clustering feedback: {str(e)}")
            return {
                "clusters": [],
                "visualization": None
            }
    
    def _generate_cluster_visualization(self, tfidf_matrix: np.ndarray, cluster_labels: np.ndarray, clusters: List[Dict[str, Any]]) -> str:
        """
        Generate a visualization of clusters
        
        Args:
            tfidf_matrix: TF-IDF matrix of review texts
            cluster_labels: Cluster assignments for each review
            clusters: List of cluster information dictionaries
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Reduce dimensions for visualization
            pca = PCA(n_components=2, random_state=42)
            reduced_features = pca.fit_transform(tfidf_matrix.toarray())
            
            # Create figure
            plt.figure(figsize=(10, 8))
            
            # Define colors for clusters
            colors = plt.cm.rainbow(np.linspace(0, 1, len(clusters)))
            
            # Plot each cluster
            for i, cluster in enumerate(clusters):
                # Get points in this cluster
                cluster_points = reduced_features[cluster_labels == cluster["id"]]
                
                if len(cluster_points) > 0:
                    # Plot points
                    plt.scatter(
                        cluster_points[:, 0], 
                        cluster_points[:, 1], 
                        s=50, 
                        color=colors[i], 
                        label=f"Cluster {i+1}: {', '.join(cluster['top_terms'][:3])}"
                    )
            
            plt.title('Review Clusters', fontsize=16)
            plt.xlabel('Component 1', fontsize=12)
            plt.ylabel('Component 2', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Save to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            
            # Encode as base64
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating cluster visualization: {str(e)}")
            return ""
