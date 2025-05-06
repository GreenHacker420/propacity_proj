import logging
from typing import List, Dict, Any, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import required packages
try:
    import langid
    LANGID_AVAILABLE = True
except ImportError:
    logger.warning("langid is not installed. Language detection will be limited.")
    LANGID_AVAILABLE = False

try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    logger.warning("googletrans is not installed. Translation will be disabled.")
    TRANSLATOR_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    logger.warning("nltk is not installed. Some language processing features will be limited.")
    NLTK_AVAILABLE = False

class LanguageProcessor:
    """
    Class for language detection and translation
    """

    def __init__(self):
        """
        Initialize the language processor
        """
        logger.info("Initializing Language Processor...")
        self.translator = None

        if TRANSLATOR_AVAILABLE:
            try:
                # Initialize translator
                self.translator = Translator()
                logger.info("Translator initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing translator: {str(e)}")
                logger.warning("Translation functionality will be disabled")

    def detect_language(self, text: str) -> str:
        """
        Detect the language of a text

        Args:
            text: The text to analyze

        Returns:
            ISO language code (e.g., 'en', 'es', 'fr')
        """
        if not text:
            return 'en'  # Default to English for empty text

        if not LANGID_AVAILABLE:
            logger.warning("Language detection is not available. Defaulting to English.")
            return 'en'

        try:
            # Detect language using langid
            lang, _ = langid.classify(text)
            return lang
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return 'en'  # Default to English on error

    def translate_text(self, text: str, target_lang: str = 'en') -> str:
        """
        Translate text to the target language

        Args:
            text: The text to translate
            target_lang: Target language code (default: 'en' for English)

        Returns:
            Translated text
        """
        if not text:
            return text

        if not TRANSLATOR_AVAILABLE or not self.translator:
            logger.warning("Translation is not available. Returning original text.")
            return text

        try:
            # Detect source language
            source_lang = self.detect_language(text)

            # Skip translation if already in target language
            if source_lang == target_lang:
                return text

            # Translate text
            translation = self.translator.translate(text, dest=target_lang, src=source_lang)
            return translation.text
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return text  # Return original text on error

    def process_multilingual_reviews(self, reviews: List[Dict[str, Any]], target_lang: str = 'en') -> List[Dict[str, Any]]:
        """
        Process multilingual reviews by detecting languages and translating non-target language reviews

        Args:
            reviews: List of review dictionaries
            target_lang: Target language code (default: 'en' for English)

        Returns:
            List of processed review dictionaries with language information and translations
        """
        if not reviews:
            return []

        processed_reviews = []
        language_counts = {}

        for review in reviews:
            if 'text' not in review or not review['text']:
                processed_reviews.append(review)
                continue

            # Detect language
            detected_lang = self.detect_language(review['text'])

            # Update language counts
            if detected_lang in language_counts:
                language_counts[detected_lang] += 1
            else:
                language_counts[detected_lang] = 1

            # Create a copy of the review
            processed_review = review.copy()

            # Add language information
            processed_review['detected_language'] = detected_lang

            # Translate if not in target language
            if detected_lang != target_lang:
                translated_text = self.translate_text(review['text'], target_lang)
                processed_review['original_text'] = review['text']
                processed_review['text'] = translated_text
                processed_review['is_translated'] = True
            else:
                processed_review['is_translated'] = False

            processed_reviews.append(processed_review)

        logger.info(f"Processed {len(processed_reviews)} reviews in {len(language_counts)} languages")
        logger.info(f"Language distribution: {language_counts}")

        return processed_reviews

    def get_language_distribution(self, reviews: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get the distribution of languages in the reviews

        Args:
            reviews: List of review dictionaries

        Returns:
            Dictionary mapping language codes to counts
        """
        if not reviews:
            return {}

        language_counts = {}

        for review in reviews:
            if 'detected_language' in review:
                lang = review['detected_language']
            elif 'text' in review and review['text']:
                lang = self.detect_language(review['text'])
            else:
                continue

            if lang in language_counts:
                language_counts[lang] += 1
            else:
                language_counts[lang] = 1

        return language_counts

    def get_language_name(self, lang_code: str) -> str:
        """
        Get the full name of a language from its ISO code

        Args:
            lang_code: ISO language code (e.g., 'en', 'es', 'fr')

        Returns:
            Full language name
        """
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'pa': 'Punjabi',
            'te': 'Telugu',
            'mr': 'Marathi',
            'ta': 'Tamil',
            'ur': 'Urdu',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'tr': 'Turkish',
            'pl': 'Polish',
            'uk': 'Ukrainian',
            'cs': 'Czech',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'el': 'Greek',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'id': 'Indonesian',
            'ms': 'Malay',
            'he': 'Hebrew',
            'fa': 'Persian'
        }

        return language_names.get(lang_code, f"Unknown ({lang_code})")
