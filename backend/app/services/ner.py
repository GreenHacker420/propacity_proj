import spacy
import logging
from typing import List, Dict, Any, Optional
import os
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NamedEntityRecognizer:
    """
    Class for performing Named Entity Recognition on text
    """
    
    def __init__(self):
        """
        Initialize the NER model
        """
        logger.info("Initializing Named Entity Recognizer...")
        try:
            # Try to load the English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy NER model successfully")
        except OSError:
            # If the model is not found, download it
            logger.info("Downloading spaCy model...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Downloaded and loaded spaCy NER model successfully")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            self.nlp = None
            logger.warning("NER functionality will be limited")
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: The text to analyze
            
        Returns:
            List of dictionaries containing entity text, label, and position
        """
        if not self.nlp or not text:
            return []
            
        try:
            # Process the text with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
                
            return entities
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def get_entity_counts(self, texts: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Get counts of entity types across multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary mapping entity types to counts of specific entities
        """
        if not self.nlp:
            return {}
            
        try:
            # Process all texts and collect entities
            all_entities = {}
            
            for text in texts:
                if not text:
                    continue
                    
                entities = self.extract_entities(text)
                
                for entity in entities:
                    entity_type = entity["label"]
                    entity_text = entity["text"].lower()
                    
                    if entity_type not in all_entities:
                        all_entities[entity_type] = Counter()
                    
                    all_entities[entity_type][entity_text] += 1
            
            # Convert Counter objects to dictionaries
            return {
                entity_type: dict(counter.most_common(10))
                for entity_type, counter in all_entities.items()
            }
        except Exception as e:
            logger.error(f"Error getting entity counts: {str(e)}")
            return {}
    
    def extract_product_mentions(self, texts: List[str]) -> Dict[str, int]:
        """
        Extract product mentions from texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary mapping product names to mention counts
        """
        if not self.nlp:
            return {}
            
        try:
            # Focus on PRODUCT, ORG, and GPE entities which often contain product names
            product_entities = Counter()
            
            for text in texts:
                if not text:
                    continue
                    
                entities = self.extract_entities(text)
                
                for entity in entities:
                    if entity["label"] in ["PRODUCT", "ORG", "GPE"]:
                        product_entities[entity["text"].lower()] += 1
            
            return dict(product_entities.most_common(20))
        except Exception as e:
            logger.error(f"Error extracting product mentions: {str(e)}")
            return {}
