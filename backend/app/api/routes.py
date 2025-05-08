from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import pandas as pd
from typing import List, Optional, Dict, Any
import tempfile
import os
import logging
import time
import re
from datetime import datetime
import io
from .models import ReviewCreate, ReviewResponse, SummaryResponse, VisualizationResponse
from ..services.analyzer import TextAnalyzer
from ..services.scraper import Scraper
from ..services.visualization import Visualizer
from ..mongodb import get_collection
from ..models.db_models import Review as DBReview, Keyword, ReviewModel
from ..auth.mongo_auth import get_current_active_user, get_current_user_optional, get_optional_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["api"],
    responses={404: {"description": "Not found"}}
)

analyzer = TextAnalyzer()
scraper = Scraper()
visualizer = Visualizer()

@router.post("/upload", response_model=List[ReviewResponse])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload and process a CSV file containing reviews.

    This endpoint accepts CSV files with various formats and automatically maps columns.
    At minimum, the CSV must contain text content for reviews.
    """
    # Always use the mock user ID for WebSocket updates
    user_id = "dev_user_123"
    logger.info(f"Received file upload: {file.filename} with mock user ID: {user_id}")

    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        # Read CSV file
        contents = await file.read()
        logger.info(f"File content length: {len(contents)}")

        # Try different encodings if UTF-8 fails
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None

        # Check if this is a Twitter training data file based on filename
        is_twitter_training = 'twitter_training' in file.filename.lower()
        if is_twitter_training:
            logger.info(f"Detected potential Twitter training data file: {file.filename}")

        for encoding in encodings:
            try:
                # Try to read with different delimiters
                for delimiter in [',', ';', '\t']:
                    try:
                        # Special handling for Twitter training data
                        if is_twitter_training:
                            try:
                                # First try reading with 4 columns and no header
                                df = pd.read_csv(io.StringIO(contents.decode(encoding)),
                                                delimiter=delimiter,
                                                header=None,
                                                names=['id', 'game', 'sentiment', 'text'])
                                logger.info(f"Successfully read Twitter training data with {encoding} encoding and '{delimiter}' delimiter (no header)")

                                # Log a sample of the data for debugging
                                if not df.empty:
                                    logger.info(f"Twitter training data sample (first 2 rows):\n{df.head(2)}")

                                    # Check if the first row looks like a header
                                    first_row = df.iloc[0]
                                    if (isinstance(first_row['id'], str) and
                                        first_row['id'].isdigit() == False and
                                        'id' in first_row['id'].lower()):
                                        logger.info("First row appears to be a header, re-reading with header")
                                        # Re-read with header
                                        df = pd.read_csv(io.StringIO(contents.decode(encoding)),
                                                        delimiter=delimiter)
                                        logger.info(f"Re-read Twitter training data with header: {df.columns.tolist()}")
                                    break
                            except Exception as e:
                                logger.warning(f"Error reading as Twitter training data: {str(e)}")
                                # Fall back to standard CSV reading

                        # Standard CSV reading
                        if df is None:
                            df = pd.read_csv(io.StringIO(contents.decode(encoding)), delimiter=delimiter)
                            logger.info(f"Successfully read CSV with {encoding} encoding and '{delimiter}' delimiter")

                            # Log a sample of the data for debugging
                            if not df.empty:
                                logger.info(f"CSV sample (first 2 rows):\n{df.head(2)}")
                                break
                    except Exception as e:
                        logger.warning(f"Error reading CSV with {encoding} encoding and '{delimiter}' delimiter: {str(e)}")
                        continue

                if df is not None:
                    break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading CSV with {encoding} encoding: {str(e)}")
                continue

        if df is None:
            raise HTTPException(status_code=400, detail="Could not decode CSV file. Please ensure it's properly formatted.")

        # Check if the CSV has headers
        if df.columns.str.contains(r'^\d+$').all() or all(col.startswith('Unnamed: ') for col in df.columns):
            logger.warning("CSV appears to have numeric or unnamed column names, which suggests no header row")
            # Try reading again with no header
            for encoding in encodings:
                try:
                    # Try different delimiters
                    for delimiter in [',', ';', '\t']:
                        try:
                            df = pd.read_csv(io.StringIO(contents.decode(encoding)), header=None, delimiter=delimiter)
                            logger.info(f"Re-read CSV with {encoding} encoding, '{delimiter}' delimiter, and no header")

                            # Check if this looks like a valid data frame
                            if not df.empty and len(df.columns) >= 3:
                                # Assign default column names based on the expected format
                                df.columns = ['id', 'category', 'text'] + [f'col_{i+4}' for i in range(len(df.columns)-3)]
                                logger.info(f"Assigned default column names: {df.columns.tolist()}")

                                # Log a sample of the data for debugging
                                logger.info(f"CSV sample with default column names (first 2 rows):\n{df.head(2)}")
                                break
                        except Exception as e:
                            logger.warning(f"Error reading CSV with no header, {encoding} encoding, and '{delimiter}' delimiter: {str(e)}")
                            continue

                    if df is not None and len(df.columns) >= 3:
                        break
                except Exception as e:
                    logger.error(f"Error reading CSV with no header and {encoding} encoding: {str(e)}")
                    continue

        logger.info(f"CSV columns: {df.columns.tolist()}")

        # Clean up column names - remove extra spaces and convert to lowercase for easier matching
        df.columns = [col.strip().lower() for col in df.columns]
        logger.info(f"Cleaned CSV columns: {df.columns.tolist()}")

        # Handle the case where column names might have spaces or special characters
        # For example, "category feedback" might be read as "category_feedback" or "category.feedback"
        column_name_mapping = {}
        for col in df.columns:
            clean_col = re.sub(r'[^a-z0-9]', '', col)
            column_name_mapping[clean_col] = col

        logger.info(f"Column name mapping: {column_name_mapping}")

        # Map columns to expected format
        column_mapping = {}

        # Special handling for Twitter training data
        if is_twitter_training and len(df.columns) == 4:
            logger.info("Using predefined column mapping for Twitter training data")
            column_mapping['id'] = 'id'
            column_mapping['category'] = 'sentiment'
            column_mapping['text'] = 'text'
            # Add game as metadata
            logger.info(f"Twitter training data column mapping: {column_mapping}")
            # Continue with the rest of the processing

        # Check if this is the specific format with id, category feedback, text
        if len(df.columns) >= 3:
            # Log the actual column names for debugging
            logger.info(f"Actual CSV column names: {df.columns.tolist()}")

            # Check if column names match the expected pattern using both original and cleaned names
            if (any('id' in col for col in df.columns) and
                any('category' in col for col in df.columns) and
                any('text' in col for col in df.columns)) or (
                'id' in column_name_mapping and
                ('category' in column_name_mapping or 'feedback' in column_name_mapping) and
                'text' in column_name_mapping):

                logger.info("Detected CSV format with ID, category, text structure by column names")

                # Map columns by name
                for col in df.columns:
                    clean_col = re.sub(r'[^a-z0-9]', '', col)

                    if 'id' in col or clean_col == 'id':
                        column_mapping['id'] = col
                    elif ('category' in col or 'feedback' in col or
                          clean_col == 'category' or clean_col == 'feedback' or
                          clean_col == 'categoryfeedback'):
                        column_mapping['category'] = col
                    elif 'text' in col or clean_col == 'text':
                        column_mapping['text'] = col

                logger.info(f"Mapped columns by name: {column_mapping}")

            # If mapping by name didn't work, try by position and content
            elif len(df.columns) >= 3:
                logger.info("Trying to detect CSV format with ID, category feedback, text structure by position and content")

                # Check each column for content characteristics
                for i, col in enumerate(df.columns):
                    # Sample the column content
                    sample_content = df[col].astype(str).str.len().mean()
                    logger.info(f"Column {i} ({col}) average content length: {sample_content}")

                    # The column with the longest average content is likely the text
                    if i == len(df.columns) - 1 and df[col].dtype == 'object':
                        # Last column is often the text in many datasets
                        column_mapping['text'] = col
                        logger.info(f"Using last column '{col}' as text based on position")
                    elif sample_content > 20 and df[col].dtype == 'object':
                        # Column with long content is likely text
                        column_mapping['text'] = col
                        logger.info(f"Using column '{col}' as text based on content length")

                # If we still don't have a text column, use the last column
                if 'text' not in column_mapping and len(df.columns) >= 3:
                    column_mapping['text'] = df.columns[-1]
                    logger.info(f"Defaulting to last column '{df.columns[-1]}' as text")

                # Look for category column - typically the second-to-last column or one with sentiment values
                if len(df.columns) >= 3:
                    potential_category_cols = []
                    for i, col in enumerate(df.columns):
                        if col != column_mapping.get('text'):
                            # Check if column contains common sentiment/category values
                            if df[col].dtype == 'object':
                                values = df[col].astype(str).str.lower()
                                has_sentiment = values.isin(['positive', 'negative', 'neutral']).any()
                                if has_sentiment:
                                    potential_category_cols.append((i, col, 2))  # High priority
                                    logger.info(f"Column '{col}' contains sentiment values")
                                elif 'category' in col.lower() or 'sentiment' in col.lower() or 'feedback' in col.lower():
                                    potential_category_cols.append((i, col, 1))  # Medium priority
                                else:
                                    potential_category_cols.append((i, col, 0))  # Low priority

                    # Sort by priority (highest first)
                    potential_category_cols.sort(key=lambda x: x[2], reverse=True)

                    if potential_category_cols:
                        column_mapping['category'] = potential_category_cols[0][1]
                        logger.info(f"Selected '{potential_category_cols[0][1]}' as category column")

                # Look for ID column - typically the first column or one with numeric values
                for i, col in enumerate(df.columns):
                    if col not in [column_mapping.get('text'), column_mapping.get('category')]:
                        if df[col].dtype in ['int64', 'float64'] or 'id' in col.lower():
                            column_mapping['id'] = col
                            logger.info(f"Selected '{col}' as ID column")
                            break

                logger.info(f"Mapped columns by position and content: {column_mapping}")

            # Special case for "id, category feedback, text" format
            elif len(df.columns) >= 3:
                logger.info("Trying special case mapping for Twitter training data format")

                # Check if this looks like Twitter training data (has 4 columns with the last being the text)
                if len(df.columns) == 4:
                    # Check if the third column contains sentiment values (Positive/Negative)
                    third_col = df.columns[2]
                    if df[third_col].dtype == 'object':
                        values = df[third_col].astype(str).str.lower()
                        has_sentiment = values.isin(['positive', 'negative', 'neutral']).any()
                        if has_sentiment:
                            logger.info(f"Detected Twitter training data format with sentiment in column '{third_col}'")
                            column_mapping['id'] = df.columns[0]
                            column_mapping['category'] = df.columns[2]  # Sentiment is in the third column
                            column_mapping['text'] = df.columns[3]      # Text is in the fourth column
                            logger.info(f"Twitter training data mapping: {column_mapping}")
                            # Don't return, just continue with the mapped columns

                # Generic 3-column case
                logger.info("Trying generic 3-column mapping for 'id, category, text' format")
                column_mapping['id'] = df.columns[0]

                # For the remaining columns, determine which is more likely to be text vs. category
                if len(df.columns) >= 3:
                    # Check content length to determine which is text
                    col1_len = df[df.columns[1]].astype(str).str.len().mean()
                    col2_len = df[df.columns[2]].astype(str).str.len().mean()

                    if col1_len > col2_len:
                        column_mapping['text'] = df.columns[1]
                        column_mapping['category'] = df.columns[2]
                    else:
                        column_mapping['category'] = df.columns[1]
                        column_mapping['text'] = df.columns[2]

                    logger.info(f"Special case mapping based on content length: {column_mapping}")

        # If we haven't mapped the text column yet, try the standard approach
        if 'text' not in column_mapping:
            # Find text column - required
            text_column_candidates = ['text', 'review', 'content', 'comment', 'description']

            # First check if there's a column explicitly named 'text'
            if 'text' in df.columns:
                column_mapping['text'] = 'text'
                logger.info("Found explicit 'text' column")
            else:
                # Try other common text column names
                for candidate in text_column_candidates:
                    if candidate in df.columns:
                        column_mapping['text'] = candidate
                        logger.info(f"Found text column: '{candidate}'")
                        break

            # Special case: if we have both 'feedback' and 'category' columns, 'feedback' is likely the text
            # But if we only have 'feedback', it might be the category
            if 'text' not in column_mapping and 'feedback' in df.columns:
                if 'category' in df.columns or any('category' in col.lower() for col in df.columns):
                    # We have both category and feedback, so feedback is likely the text
                    column_mapping['text'] = 'feedback'
                    logger.info("Using 'feedback' column as text since 'category' also exists")
                else:
                    # Check if feedback column has longer text that looks like reviews
                    if df['feedback'].dtype == 'object' and df['feedback'].str.len().mean() > 20:
                        column_mapping['text'] = 'feedback'
                        logger.info("Using 'feedback' column as text based on content length")

            if 'text' not in column_mapping:
                # If no exact match, look for columns containing these words
                for col in df.columns:
                    if any(candidate in col.lower() for candidate in text_column_candidates):
                        column_mapping['text'] = col
                        break

            if 'text' not in column_mapping:
                # If still no match, use the first string column with reasonable content
                for col in df.columns:
                    if df[col].dtype == 'object' and df[col].str.len().mean() > 10:
                        column_mapping['text'] = col
                        break

            if 'text' not in column_mapping:
                raise HTTPException(status_code=400,
                                detail="Could not identify a text column in the CSV. Please ensure your CSV contains review text.")

            # Find username column - optional
            username_column_candidates = ['username', 'user', 'name', 'author', 'reviewer']
            for candidate in username_column_candidates:
                if candidate in df.columns:
                    column_mapping['username'] = candidate
                    break

            # Find category column - optional
            category_column_candidates = ['category', 'feedback', 'sentiment', 'type', 'class', 'category feedback', 'categoryfeedback']
            for candidate in category_column_candidates:
                if candidate in df.columns:
                    column_mapping['category'] = candidate
                    logger.info(f"Found category column: '{candidate}'")
                    break

            # Check for partial matches if no exact match
            if 'category' not in column_mapping:
                for col in df.columns:
                    if any(candidate in col.lower() for candidate in ['category', 'feedback']):
                        column_mapping['category'] = col
                        logger.info(f"Found category column by partial match: '{col}'")
                        break

        # Find rating column - optional
        rating_column_candidates = ['rating', 'score', 'stars', 'grade', 'rank']
        for candidate in rating_column_candidates:
            if candidate in df.columns:
                column_mapping['rating'] = candidate
                break

        # Find timestamp column - optional
        timestamp_column_candidates = ['timestamp', 'date', 'time', 'datetime', 'created_at']
        for candidate in timestamp_column_candidates:
            if candidate in df.columns:
                column_mapping['timestamp'] = candidate
                break

        logger.info(f"Column mapping: {column_mapping}")

        # Create reviews from CSV data
        reviews = []

        # Log the final column mapping for debugging
        logger.info(f"Final column mapping to be used: {column_mapping}")

        # Check if we have the required text column
        if 'text' not in column_mapping:
            logger.error("No text column found in the CSV. Cannot process reviews.")
            raise HTTPException(status_code=400, detail="Could not identify a text column in the CSV. Please ensure your CSV contains review text.")

        for idx, row in df.iterrows():
            # Log the raw row data for debugging (first few rows only)
            if idx < 3:
                logger.info(f"Processing row {idx}: {row.to_dict()}")

            # Skip rows with empty text
            if pd.isna(row[column_mapping['text']]) or str(row[column_mapping['text']]).strip() == '':
                logger.warning(f"Skipping row {idx} due to empty text")
                continue

            # Create the basic review data structure
            review_data = {
                'text': str(row[column_mapping['text']]),
                'username': str(row[column_mapping['username']]) if 'username' in column_mapping and not pd.isna(row[column_mapping['username']]) else None,
                'rating': float(row[column_mapping['rating']]) if 'rating' in column_mapping and not pd.isna(row[column_mapping['rating']]) else None,
                'timestamp': row[column_mapping['timestamp']] if 'timestamp' in column_mapping and not pd.isna(row[column_mapping['timestamp']]) else None,
                'source': 'csv'  # Add source information
            }

            # Add metadata for additional columns
            metadata = {}

            # Add ID if available
            if 'id' in column_mapping and not pd.isna(row[column_mapping['id']]):
                id_value = str(row[column_mapping['id']])
                metadata['id'] = id_value
                logger.info(f"Row {idx} - ID value: '{id_value}'")

            # Special handling for Twitter training data - add game information
            if is_twitter_training and 'game' in df.columns and not pd.isna(row['game']):
                game_value = str(row['game']).strip()
                metadata['game'] = game_value
                logger.info(f"Row {idx} - Game value: '{game_value}'")

            # Add category feedback if available
            if 'category' in column_mapping and not pd.isna(row[column_mapping['category']]):
                category_value = str(row[column_mapping['category']]).strip()
                metadata['category_feedback'] = category_value

                # Log the category value for debugging
                logger.info(f"Row {idx} - Category value: '{category_value}'")

                # Try to map the category to our internal categories
                if category_value.lower() in ['positive', 'pos', 'good', 'p']:
                    metadata['predefined_category'] = 'positive_feedback'
                elif category_value.lower() in ['negative', 'neg', 'bad', 'n']:
                    metadata['predefined_category'] = 'pain_point'
                elif category_value.lower() in ['request', 'feature', 'suggestion', 'r']:
                    metadata['predefined_category'] = 'feature_request'
                # Add more mappings for common category values
                elif any(term in category_value.lower() for term in ['bug', 'issue', 'problem', 'error', 'crash', 'fail']):
                    metadata['predefined_category'] = 'pain_point'
                elif any(term in category_value.lower() for term in ['enhancement', 'improvement', 'add', 'new', 'want']):
                    metadata['predefined_category'] = 'feature_request'
                elif any(term in category_value.lower() for term in ['praise', 'compliment', 'like', 'love', 'great']):
                    metadata['predefined_category'] = 'positive_feedback'

                # Log the mapped category
                if 'predefined_category' in metadata:
                    logger.info(f"Row {idx} - Mapped to category: '{metadata['predefined_category']}'")
                else:
                    logger.info(f"Row {idx} - No category mapping found for: '{category_value}'")

            # Add any other columns as additional metadata
            for col in df.columns:
                if col not in [column_mapping.get('text'), column_mapping.get('username'),
                              column_mapping.get('rating'), column_mapping.get('timestamp'),
                              column_mapping.get('id'), column_mapping.get('category')]:
                    if not pd.isna(row[col]):
                        metadata[f'extra_{col}'] = str(row[col])

            # Add metadata to review data
            review_data['metadata'] = metadata

            # Log the final review data structure (first few rows only)
            if idx < 3:
                logger.info(f"Final review data for row {idx}: {review_data}")

            try:
                review = ReviewCreate(**review_data)
                # Store the review for batch processing
                reviews.append(review)
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue

        # Extract texts and metadata for batch processing
        texts = [review.text for review in reviews]
        metadata_list = [review.metadata for review in reviews]

        # Always add the mock user_id to metadata for WebSocket updates
        for metadata in metadata_list:
            metadata['user_id'] = user_id

        # Use batch processing for better performance
        logger.info(f"Analyzing {len(texts)} reviews from CSV in batch")
        start_time = time.time()

        # Process all texts in batch with metadata
        analyses = analyzer.analyze_texts_batch(texts, metadata_list)

        processing_time = time.time() - start_time
        logger.info(f"Batch analysis of CSV reviews completed in {processing_time:.2f} seconds")

        # Combine review data with analyses
        analyzed_reviews = []
        for i, review in enumerate(reviews):
            review_dict = review.model_dump()
            review_dict.update(analyses[i])
            analyzed_reviews.append(review_dict)

        logger.info(f"Processed {len(analyzed_reviews)} reviews from CSV")
        return analyzed_reviews
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scrape", response_model=List[ReviewResponse])
async def scrape_data(
    source: str = Query(..., description="Data source (twitter, playstore)"),
    query: Optional[str] = Query(None, description="Search query or app URL"),
    limit: int = Query(50, ge=1, le=5000, description="Maximum number of reviews to fetch")
):
    """
    Scrape and analyze data from online sources

    This endpoint does not require authentication.
    """
    # Use a mock user ID for WebSocket updates
    user_id = "dev_user_123"
    logger.info(f"Scraping with user_id: {user_id} (no authentication required)")
    try:
        if source == 'playstore':
            if not query:
                raise HTTPException(status_code=400, detail="App URL is required for Play Store scraping")
            try:
                # Extract app ID from URL if needed
                app_id = scraper.extract_app_id(query)
                reviews = scraper.scrape_playstore(app_id, limit)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        elif source == 'twitter':
            if not query:
                raise HTTPException(status_code=400, detail="Search query is required for Twitter scraping")
            reviews = scraper.scrape_twitter(query, limit)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")

        # Extract texts for batch processing
        texts = [review['text'] for review in reviews]

        # Create metadata list with user_id for WebSocket updates
        metadata_list = []
        for _ in range(len(texts)):
            metadata = {'source': source}
            if user_id:
                metadata['user_id'] = user_id
            metadata_list.append(metadata)

        # Use batch processing for better performance
        logger.info(f"Analyzing {len(texts)} scraped reviews in batch")
        start_time = time.time()

        # Process all texts in batch with metadata
        analyses = analyzer.analyze_texts_batch(texts, metadata_list)

        processing_time = time.time() - start_time
        logger.info(f"Batch analysis of scraped reviews completed in {processing_time:.2f} seconds")

        # Combine review data with analyses
        analyzed_reviews = []
        for i, review in enumerate(reviews):
            analysis = analyses[i]
            analyzed_reviews.append({
                "text": review['text'],
                "sentiment_score": analysis['sentiment_score'],
                "sentiment_label": analysis['sentiment_label'],
                "category": analysis['category'],
                "keywords": analysis['keywords'],
                "source": source,
                "metadata": {
                    "author": review.get('author', review.get('username')),
                    "date": review.get('date', review.get('timestamp')),
                    "rating": review.get('rating'),
                    "thumbs_up": review.get('thumbs_up'),
                    "app_version": review.get('app_version'),
                    "app_name": review.get('app_name'),
                    "app_developer": review.get('app_developer'),
                    "app_category": review.get('app_category'),
                    "app_rating": review.get('app_rating'),
                    "app_installs": review.get('app_installs')
                }
            })

        return analyzed_reviews
    except Exception as e:
        logger.error(f"Error scraping data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=List[ReviewResponse])
async def analyze_reviews(reviews: List[ReviewCreate], current_user: Optional[dict] = Depends(get_current_user_optional)):
    try:
        # Get user ID for WebSocket updates
        user_id = str(current_user["_id"]) if current_user else None

        # Extract texts and metadata for batch processing
        texts = [review.text for review in reviews]
        metadata_list = [review.metadata for review in reviews if hasattr(review, 'metadata')]

        # Add user_id to metadata for WebSocket updates
        if user_id:
            for metadata in metadata_list:
                metadata['user_id'] = user_id

        # Use batch processing for better performance
        logger.info(f"Analyzing {len(texts)} reviews in batch")
        start_time = time.time()

        # Process all texts in batch with metadata
        analyses = analyzer.analyze_texts_batch(texts, metadata_list)

        processing_time = time.time() - start_time
        logger.info(f"Batch analysis completed in {processing_time:.2f} seconds")

        # Combine review data with analyses
        analyzed_reviews = []
        for i, review in enumerate(reviews):
            review_dict = review.model_dump()
            review_dict.update(analyses[i])
            analyzed_reviews.append(review_dict)

        return analyzed_reviews

    except Exception as e:
        logger.error(f"Error analyzing reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary", response_model=SummaryResponse)
async def get_summary(reviews: List[ReviewResponse]):
    try:
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")

        return analyzer.generate_summary(reviews)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categorize", response_model=List[ReviewResponse])
async def categorize_reviews(reviews: List[ReviewResponse]):
    """
    Categorize reviews into pain points, feature requests, and positive feedback
    """
    try:
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")

        # Use the analyzer to categorize reviews
        categorized_reviews = analyzer.categorize_reviews(reviews)
        return categorized_reviews

    except Exception as e:
        logger.error(f"Error categorizing reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary/pdf")
async def get_summary_pdf(reviews: List[ReviewResponse]):
    try:
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")

        # Generate summary
        summary = analyzer.generate_summary(reviews)

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    .section {{ margin-bottom: 30px; }}
                    .item {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
                    .pain-point {{ background: #ffebee; }}
                    .feature-request {{ background: #e3f2fd; }}
                    .positive-feedback {{ background: #e8f5e9; }}
                    .priority {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>Weekly Product Review Summary</h1>
                <div class="section">
                    <h2>Top Pain Points</h2>
                    {''.join(f'<div class="item pain-point"><p>{item["text"]}</p><p>Sentiment: {item["sentiment_score"]:.2f}</p></div>' for item in summary["pain_points"])}
                </div>
                <div class="section">
                    <h2>Top Feature Requests</h2>
                    {''.join(f'<div class="item feature-request"><p>{item["text"]}</p><p>Sentiment: {item["sentiment_score"]:.2f}</p></div>' for item in summary["feature_requests"])}
                </div>
                <div class="section">
                    <h2>Positive Feedback</h2>
                    {''.join(f'<div class="item positive-feedback"><p>{item["text"]}</p><p>Sentiment: {item["sentiment_score"]:.2f}</p></div>' for item in summary["positive_feedback"])}
                </div>
                <div class="section">
                    <h2>Suggested Priorities for Product Managers</h2>
                    {''.join(f'<div class="item priority">{priority}</div>' for priority in summary["suggested_priorities"])}
                </div>
                <div class="footer">
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
                </div>
            </body>
            </html>
            """
            f.write(html_content.encode())
            temp_html = f.name

        # Convert HTML to PDF
        from weasyprint import HTML
        pdf_path = temp_html.replace('.html', '.pdf')
        HTML(temp_html).write_pdf(pdf_path)

        # Clean up temporary HTML file
        os.unlink(temp_html)

        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f'product_review_summary_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visualize", response_model=VisualizationResponse)
async def visualize_reviews(reviews: List[ReviewResponse]):
    """
    Generate visualizations from review data

    This endpoint creates various charts and graphs based on the provided reviews,
    including sentiment distribution, rating distribution, and keyword frequency.

    Returns:
        Base64 encoded PNG images for each visualization type
    """
    try:
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")

        logger.info(f"Generating visualizations for {len(reviews)} reviews")

        # Generate charts
        sentiment_chart = visualizer.generate_sentiment_chart(reviews)
        rating_chart = visualizer.generate_rating_chart(reviews)
        keyword_chart = visualizer.generate_keyword_chart(reviews)

        return VisualizationResponse(
            sentiment_chart=sentiment_chart,
            rating_chart=rating_chart,
            keyword_chart=keyword_chart
        )

    except Exception as e:
        logger.error(f"Error generating visualizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))