import logging
import re
import torch
from typing import Dict, List, Any, Tuple, Optional
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSentimentAnalyzer:
    """
    Advanced sentiment analysis with context awareness and sarcasm detection
    """

    def __init__(self):
        """
        Initialize the advanced sentiment analyzer
        """
        logger.info("Initializing Advanced Sentiment Analyzer...")

        # Initialize VADER sentiment analyzer for rule-based analysis
        try:
            self.vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except Exception as e:
            logger.error(f"Error initializing VADER: {str(e)}")
            self.vader_analyzer = None

        # Initialize Hugging Face transformer model for deep learning-based analysis
        try:
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True
            )
            logger.info("Transformer sentiment model initialized")
        except Exception as e:
            logger.error(f"Error initializing transformer model: {str(e)}")
            self.sentiment_model = None

        # Initialize sarcasm detection model
        try:
            self.sarcasm_model = pipeline(
                "text-classification",
                model="mrm8488/distilroberta-finetuned-sarcasm",
                return_all_scores=True
            )
            logger.info("Sarcasm detection model initialized")
        except Exception as e:
            logger.error(f"Error initializing sarcasm model: {str(e)}")
            self.sarcasm_model = None

        # Initialize spaCy for context analysis
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model initialized")
        except Exception as e:
            logger.error(f"Error initializing spaCy: {str(e)}")
            self.nlp = None

        # Keywords for context-aware analysis
        self.positive_intensifiers = {
            'very', 'really', 'extremely', 'absolutely', 'incredibly', 'truly',
            'highly', 'especially', 'particularly', 'completely', 'totally'
        }

        self.negative_intensifiers = {
            'barely', 'hardly', 'scarcely', 'slightly', 'somewhat', 'just',
            'only', 'marginally', 'rarely', 'seldom'
        }

        self.negation_words = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither', 'nor',
            'nowhere', 'cannot', "can't", "don't", "doesn't", "didn't", "won't",
            "wouldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't"
        }

        # Sarcasm indicators
        self.sarcasm_indicators = {
            'yeah right', 'oh really', 'sure thing', 'oh great', 'just what i needed',
            'wow', 'amazing', 'fantastic', 'wonderful', 'brilliant', 'genius',
            'perfect', 'exactly', 'absolutely', 'definitely', 'totally'
        }

        # Punctuation patterns for sarcasm detection
        self.punctuation_patterns = [
            r'\.{3,}',  # Ellipsis
            r'!{2,}',   # Multiple exclamation marks
            r'\?{2,}',  # Multiple question marks
            r'!\?|\?!', # Mixed punctuation
        ]

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Perform advanced sentiment analysis on text

        Args:
            text: The text to analyze

        Returns:
            Dictionary with sentiment analysis results
        """
        if not text or not text.strip():
            return {
                "sentiment_score": 0.5,
                "sentiment_label": "NEUTRAL",
                "confidence": 0.0,
                "is_sarcastic": False,
                "sarcasm_confidence": 0.0,
                "context_analysis": {},
                "aspect_sentiments": []
            }

        # Clean the text
        cleaned_text = self._clean_text(text)

        # Check for sarcasm
        is_sarcastic, sarcasm_confidence = self._detect_sarcasm(cleaned_text)

        # Get transformer-based sentiment if available
        transformer_sentiment = self._get_transformer_sentiment(cleaned_text)

        # Get VADER sentiment
        vader_sentiment = self._get_vader_sentiment(cleaned_text)

        # Perform context analysis
        context_analysis = self._analyze_context(cleaned_text)

        # Extract aspect-based sentiments
        aspect_sentiments = self._extract_aspect_sentiments(cleaned_text)

        # Combine all signals for final sentiment
        final_sentiment = self._combine_sentiment_signals(
            transformer_sentiment,
            vader_sentiment,
            context_analysis,
            is_sarcastic
        )

        return {
            "sentiment_score": final_sentiment["score"],
            "sentiment_label": final_sentiment["label"],
            "confidence": final_sentiment["confidence"],
            "is_sarcastic": is_sarcastic,
            "sarcasm_confidence": sarcasm_confidence,
            "context_analysis": context_analysis,
            "aspect_sentiments": aspect_sentiments
        }

    def _clean_text(self, text: str) -> str:
        """Clean the text for analysis"""
        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _detect_sarcasm(self, text: str) -> Tuple[bool, float]:
        """Detect sarcasm in text"""
        # Rule-based sarcasm detection
        sarcasm_score = 0.0

        # Check for sarcasm indicators
        for indicator in self.sarcasm_indicators:
            if indicator in text:
                sarcasm_score += 0.2

        # Check for punctuation patterns
        for pattern in self.punctuation_patterns:
            if re.search(pattern, text):
                sarcasm_score += 0.15

        # Check for mixed case (e.g., "SuRe ThInG")
        if re.search(r'[A-Z][a-z][A-Z]', text):
            sarcasm_score += 0.25

        # Use sarcasm model if available
        if self.sarcasm_model:
            try:
                results = self.sarcasm_model(text[:512])
                model_sarcasm_score = next((item['score'] for item in results[0] if item['label'] == 'SARCASM'), 0.0)

                # Combine rule-based and model-based scores
                sarcasm_score = 0.3 * sarcasm_score + 0.7 * model_sarcasm_score
            except Exception as e:
                logger.error(f"Error in sarcasm detection model: {str(e)}")

        # Cap the score at 1.0
        sarcasm_score = min(sarcasm_score, 1.0)

        return sarcasm_score > 0.5, sarcasm_score

    def _get_transformer_sentiment(self, text: str) -> Dict[str, Any]:
        """Get sentiment using transformer model"""
        if not self.sentiment_model:
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

        try:
            results = self.sentiment_model(text[:512])

            # Extract scores for POSITIVE and NEGATIVE labels
            scores = {item['label']: item['score'] for item in results[0]}

            if 'POSITIVE' in scores:
                score = scores['POSITIVE']
                label = "POSITIVE" if score > 0.5 else "NEGATIVE"
                confidence = scores['POSITIVE'] if label == "POSITIVE" else scores['NEGATIVE']
            else:
                # Handle different label formats
                positive_score = next((item['score'] for item in results[0] if item['label'].lower() in ['positive', 'pos']), 0.5)
                score = positive_score
                label = "POSITIVE" if score > 0.5 else "NEGATIVE"
                confidence = score if label == "POSITIVE" else (1.0 - score)

            # Adjust score to be between 0 and 1
            if label == "NEGATIVE":
                score = 1.0 - score

            # Set NEUTRAL for borderline cases
            if 0.4 <= score <= 0.6:
                label = "NEUTRAL"
                confidence = 1.0 - abs(score - 0.5) * 2  # Confidence decreases as we get closer to 0.5

            return {"score": score, "label": label, "confidence": confidence}
        except Exception as e:
            logger.error(f"Error in transformer sentiment analysis: {str(e)}")
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

    def _get_vader_sentiment(self, text: str) -> Dict[str, Any]:
        """Get sentiment using VADER"""
        if not self.vader_analyzer:
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

        try:
            sentiment_scores = self.vader_analyzer.polarity_scores(text)
            compound_score = sentiment_scores['compound']

            # Convert compound score from [-1, 1] to [0, 1]
            normalized_score = (compound_score + 1) / 2

            # Determine sentiment label
            if compound_score >= 0.05:
                label = "POSITIVE"
            elif compound_score <= -0.05:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"

            # Calculate confidence based on the magnitude of the compound score
            confidence = abs(compound_score)

            return {"score": normalized_score, "label": label, "confidence": confidence}
        except Exception as e:
            logger.error(f"Error in VADER sentiment analysis: {str(e)}")
            return {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}

    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze context for sentiment modifiers"""
        context_analysis = {
            "has_negation": False,
            "has_intensifiers": False,
            "intensifier_type": None,
            "negated_sentiment": None
        }

        if not self.nlp:
            return context_analysis

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Check for negation
            negation_words_found = [token.text for token in doc if token.text.lower() in self.negation_words]
            context_analysis["has_negation"] = len(negation_words_found) > 0

            # Check for intensifiers
            positive_intensifiers_found = [token.text for token in doc if token.text.lower() in self.positive_intensifiers]
            negative_intensifiers_found = [token.text for token in doc if token.text.lower() in self.negative_intensifiers]

            context_analysis["has_intensifiers"] = len(positive_intensifiers_found) > 0 or len(negative_intensifiers_found) > 0

            if len(positive_intensifiers_found) > len(negative_intensifiers_found):
                context_analysis["intensifier_type"] = "positive"
            elif len(negative_intensifiers_found) > len(positive_intensifiers_found):
                context_analysis["intensifier_type"] = "negative"

            # Analyze negated sentiment
            if context_analysis["has_negation"]:
                # Get VADER sentiment without considering negation
                vader_sentiment = self._get_vader_sentiment(text)

                # Flip the sentiment if negation is present
                if vader_sentiment["label"] == "POSITIVE":
                    context_analysis["negated_sentiment"] = "NEGATIVE"
                elif vader_sentiment["label"] == "NEGATIVE":
                    context_analysis["negated_sentiment"] = "POSITIVE"

            return context_analysis
        except Exception as e:
            logger.error(f"Error in context analysis: {str(e)}")
            return context_analysis

    def _extract_aspect_sentiments(self, text: str) -> List[Dict[str, Any]]:
        """Extract aspect-based sentiments"""
        if not self.nlp:
            return []

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            aspect_sentiments = []

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
                if self.vader_analyzer:
                    sentiment_scores = self.vader_analyzer.polarity_scores(context)
                    compound_score = sentiment_scores['compound']

                    # Convert compound score from [-1, 1] to [0, 1]
                    normalized_score = (compound_score + 1) / 2

                    # Determine sentiment label
                    if compound_score >= 0.05:
                        label = "POSITIVE"
                    elif compound_score <= -0.05:
                        label = "NEGATIVE"
                    else:
                        label = "NEUTRAL"

                    aspect_sentiments.append({
                        "aspect": aspect,
                        "context": context,
                        "sentiment_score": normalized_score,
                        "sentiment_label": label
                    })

            return aspect_sentiments
        except Exception as e:
            logger.error(f"Error extracting aspect sentiments: {str(e)}")
            return []

    def _combine_sentiment_signals(
        self,
        transformer_sentiment: Dict[str, Any],
        vader_sentiment: Dict[str, Any],
        context_analysis: Dict[str, Any],
        is_sarcastic: bool
    ) -> Dict[str, Any]:
        """Combine all sentiment signals for final sentiment"""
        # Start with transformer sentiment as base
        final_score = transformer_sentiment["score"]
        final_label = transformer_sentiment["label"]
        final_confidence = transformer_sentiment["confidence"]

        # Adjust for VADER sentiment (weighted average)
        final_score = 0.7 * final_score + 0.3 * vader_sentiment["score"]

        # Adjust for context
        if context_analysis["has_negation"]:
            # Flip the sentiment score for negation
            final_score = 1.0 - final_score

            # Update label based on new score
            if final_score >= 0.6:
                final_label = "POSITIVE"
            elif final_score <= 0.4:
                final_label = "NEGATIVE"
            else:
                final_label = "NEUTRAL"

        if context_analysis["has_intensifiers"]:
            if context_analysis["intensifier_type"] == "positive":
                # Intensify the sentiment (move away from neutral)
                if final_score > 0.5:
                    final_score = 0.5 + (final_score - 0.5) * 1.5  # Boost positive sentiment
                else:
                    final_score = 0.5 - (0.5 - final_score) * 1.5  # Boost negative sentiment
            elif context_analysis["intensifier_type"] == "negative":
                # Diminish the sentiment (move toward neutral)
                final_score = 0.5 + (final_score - 0.5) * 0.5

        # Adjust for sarcasm
        if is_sarcastic:
            # Flip the sentiment for sarcasm
            final_score = 1.0 - final_score

            # Update label based on new score
            if final_score >= 0.6:
                final_label = "POSITIVE"
            elif final_score <= 0.4:
                final_label = "NEGATIVE"
            else:
                final_label = "NEUTRAL"

            # Reduce confidence for sarcastic text
            final_confidence *= 0.8

        # Ensure score is in [0, 1]
        final_score = max(0.0, min(1.0, final_score))

        # Update label based on final score
        if final_score >= 0.6:
            final_label = "POSITIVE"
        elif final_score <= 0.4:
            final_label = "NEGATIVE"
        else:
            final_label = "NEUTRAL"

        return {
            "score": final_score,
            "label": final_label,
            "confidence": final_confidence
        }

    def analyze_sentiment_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Perform batch sentiment analysis on multiple texts

        Args:
            texts: List of texts to analyze

        Returns:
            List of dictionaries with sentiment analysis results
        """
        logger.info(f"Processing batch of {len(texts)} texts")

        # Initialize results list
        results = []

        # Process texts in batches of 20 for better performance
        batch_size = 20

        # Pre-process all texts
        cleaned_texts = [self._clean_text(text) if text and text.strip() else "" for text in texts]

        # Batch process transformer sentiment if available
        transformer_sentiments = []
        if self.sentiment_model:
            try:
                # Process non-empty texts in batches
                valid_indices = [i for i, text in enumerate(cleaned_texts) if text]
                valid_texts = [cleaned_texts[i] for i in valid_indices]

                if valid_texts:
                    logger.info(f"Batch processing {len(valid_texts)} non-empty texts with transformer model")

                    # Process in batches to avoid memory issues
                    batch_results = []
                    for i in range(0, len(valid_texts), batch_size):
                        batch = valid_texts[i:i+batch_size]
                        # Truncate texts to 512 tokens for transformer model
                        truncated_batch = [text[:512] for text in batch]
                        batch_result = self.sentiment_model(truncated_batch)
                        batch_results.extend(batch_result)

                    # Process results
                    valid_transformer_sentiments = []
                    for results in batch_results:
                        # Check if results is already a dictionary with 'label' and 'score'
                        if isinstance(results, dict) and 'label' in results and 'score' in results:
                            # Direct format from transformer model
                            label = results['label']
                            score = results['score']
                            confidence = results.get('confidence', score)
                        else:
                            # Extract scores for POSITIVE and NEGATIVE labels
                            try:
                                scores = {item['label']: item['score'] for item in results}

                                if 'POSITIVE' in scores:
                                    score = scores['POSITIVE']
                                    label = "POSITIVE" if score > 0.5 else "NEGATIVE"
                                    confidence = scores['POSITIVE'] if label == "POSITIVE" else scores['NEGATIVE']
                                else:
                                    # Handle different label formats
                                    positive_score = next((item['score'] for item in results if item['label'].lower() in ['positive', 'pos']), 0.5)
                                    score = positive_score
                                    label = "POSITIVE" if score > 0.5 else "NEGATIVE"
                                    confidence = score if label == "POSITIVE" else (1.0 - score)
                            except (TypeError, KeyError) as e:
                                # Handle unexpected format
                                logger.warning(f"Unexpected result format: {results}. Error: {str(e)}")
                                score = 0.5
                                label = "NEUTRAL"
                                confidence = 0.0

                        # Adjust score to be between 0 and 1
                        if label == "NEGATIVE":
                            score = 1.0 - score

                        # Set NEUTRAL for borderline cases
                        if 0.4 <= score <= 0.6:
                            label = "NEUTRAL"
                            confidence = 1.0 - abs(score - 0.5) * 2  # Confidence decreases as we get closer to 0.5

                        valid_transformer_sentiments.append({"score": score, "label": label, "confidence": confidence})

                    # Map back to original indices
                    transformer_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]
                    for i, sentiment in zip(valid_indices, valid_transformer_sentiments):
                        transformer_sentiments[i] = sentiment
                else:
                    transformer_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]
            except Exception as e:
                logger.error(f"Error in batch transformer sentiment analysis: {str(e)}")
                transformer_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]
        else:
            transformer_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]

        # Batch process VADER sentiment
        vader_sentiments = []
        if self.vader_analyzer:
            try:
                logger.info("Batch processing with VADER sentiment analyzer")
                for text in cleaned_texts:
                    if not text:
                        vader_sentiments.append({"score": 0.5, "label": "NEUTRAL", "confidence": 0.0})
                        continue

                    sentiment_scores = self.vader_analyzer.polarity_scores(text)
                    compound_score = sentiment_scores['compound']

                    # Convert compound score from [-1, 1] to [0, 1]
                    normalized_score = (compound_score + 1) / 2

                    # Determine sentiment label
                    if compound_score >= 0.05:
                        label = "POSITIVE"
                    elif compound_score <= -0.05:
                        label = "NEGATIVE"
                    else:
                        label = "NEUTRAL"

                    # Calculate confidence based on the magnitude of the compound score
                    confidence = abs(compound_score)

                    vader_sentiments.append({"score": normalized_score, "label": label, "confidence": confidence})
            except Exception as e:
                logger.error(f"Error in batch VADER sentiment analysis: {str(e)}")
                vader_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]
        else:
            vader_sentiments = [{"score": 0.5, "label": "NEUTRAL", "confidence": 0.0} for _ in texts]

        # Batch process sarcasm detection
        sarcasm_results = []
        if self.sarcasm_model:
            try:
                # Process non-empty texts in batches
                valid_indices = [i for i, text in enumerate(cleaned_texts) if text]
                valid_texts = [cleaned_texts[i] for i in valid_indices]

                if valid_texts:
                    logger.info(f"Batch processing {len(valid_texts)} non-empty texts with sarcasm model")

                    # Process in batches to avoid memory issues
                    batch_results = []
                    for i in range(0, len(valid_texts), batch_size):
                        batch = valid_texts[i:i+batch_size]
                        # Truncate texts to 512 tokens for transformer model
                        truncated_batch = [text[:512] for text in batch]
                        batch_result = self.sarcasm_model(truncated_batch)
                        batch_results.extend(batch_result)

                    # Process results
                    valid_sarcasm_results = []
                    for results in batch_results:
                        model_sarcasm_score = next((item['score'] for item in results if item['label'] == 'SARCASM'), 0.0)
                        valid_sarcasm_results.append((model_sarcasm_score > 0.5, model_sarcasm_score))

                    # Map back to original indices
                    sarcasm_results = [(False, 0.0) for _ in texts]
                    for i, result in zip(valid_indices, valid_sarcasm_results):
                        sarcasm_results[i] = result
                else:
                    sarcasm_results = [(False, 0.0) for _ in texts]
            except Exception as e:
                logger.error(f"Error in batch sarcasm detection: {str(e)}")
                sarcasm_results = [(False, 0.0) for _ in texts]
        else:
            # Fall back to rule-based sarcasm detection
            for text in cleaned_texts:
                if not text:
                    sarcasm_results.append((False, 0.0))
                    continue

                # Rule-based sarcasm detection
                sarcasm_score = 0.0

                # Check for sarcasm indicators
                for indicator in self.sarcasm_indicators:
                    if indicator in text:
                        sarcasm_score += 0.2

                # Check for punctuation patterns
                for pattern in self.punctuation_patterns:
                    if re.search(pattern, text):
                        sarcasm_score += 0.15

                # Check for mixed case (e.g., "SuRe ThInG")
                if re.search(r'[A-Z][a-z][A-Z]', text):
                    sarcasm_score += 0.25

                # Cap the score at 1.0
                sarcasm_score = min(sarcasm_score, 1.0)

                sarcasm_results.append((sarcasm_score > 0.5, sarcasm_score))

        # Process context analysis and aspect sentiments for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append({
                    "sentiment_score": 0.5,
                    "sentiment_label": "NEUTRAL",
                    "confidence": 0.0,
                    "is_sarcastic": False,
                    "sarcasm_confidence": 0.0,
                    "context_analysis": {},
                    "aspect_sentiments": []
                })
                continue

            cleaned_text = cleaned_texts[i]

            # Get context analysis
            context_analysis = self._analyze_context(cleaned_text)

            # Get aspect sentiments
            aspect_sentiments = self._extract_aspect_sentiments(cleaned_text)

            # Get sarcasm results
            is_sarcastic, sarcasm_confidence = sarcasm_results[i]

            # Combine all signals for final sentiment
            final_sentiment = self._combine_sentiment_signals(
                transformer_sentiments[i],
                vader_sentiments[i],
                context_analysis,
                is_sarcastic
            )

            # Create final result
            result = {
                "sentiment_score": final_sentiment["score"],
                "sentiment_label": final_sentiment["label"],
                "confidence": final_sentiment["confidence"],
                "is_sarcastic": is_sarcastic,
                "sarcasm_confidence": sarcasm_confidence,
                "context_analysis": context_analysis,
                "aspect_sentiments": aspect_sentiments
            }

            results.append(result)

        logger.info(f"Completed batch processing of {len(texts)} texts")
        return results

# Create an instance of the advanced sentiment analyzer
advanced_sentiment_analyzer = AdvancedSentimentAnalyzer()
