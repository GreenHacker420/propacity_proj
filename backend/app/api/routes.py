from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import pandas as pd
from typing import List, Optional, Dict, Any
import tempfile
import os
import logging
from datetime import datetime
import io
from .models import ReviewCreate, ReviewResponse, SummaryResponse, VisualizationResponse
from ..services.analyzer import TextAnalyzer
from ..services.scraper import Scraper
from ..services.visualization import Visualizer
from ..mongodb import get_collection
from ..models.db_models import Review as DBReview, Keyword, ReviewModel
from ..auth.mongo_auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
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
    logger.info(f"Received file upload: {file.filename}")

    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        # Read CSV file
        contents = await file.read()
        logger.info(f"File content length: {len(contents)}")

        # Try different encodings if UTF-8 fails
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(io.StringIO(contents.decode(encoding)))
                logger.info(f"Successfully read CSV with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading CSV with {encoding} encoding: {str(e)}")
                continue

        if df is None:
            raise HTTPException(status_code=400, detail="Could not decode CSV file. Please ensure it's properly formatted.")

        logger.info(f"CSV columns: {df.columns.tolist()}")

        # Map columns to expected format
        column_mapping = {}

        # Find text column - required
        text_column_candidates = ['text', 'review', 'content', 'comment', 'feedback', 'description']
        for candidate in text_column_candidates:
            if candidate in df.columns:
                column_mapping['text'] = candidate
                break

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
        for _, row in df.iterrows():
            # Skip rows with empty text
            if pd.isna(row[column_mapping['text']]) or str(row[column_mapping['text']]).strip() == '':
                continue

            review_data = {
                'text': str(row[column_mapping['text']]),
                'username': str(row[column_mapping['username']]) if 'username' in column_mapping and not pd.isna(row[column_mapping['username']]) else None,
                'rating': float(row[column_mapping['rating']]) if 'rating' in column_mapping and not pd.isna(row[column_mapping['rating']]) else None,
                'timestamp': row[column_mapping['timestamp']] if 'timestamp' in column_mapping and not pd.isna(row[column_mapping['timestamp']]) else None
            }

            try:
                review = ReviewCreate(**review_data)

                # Analyze the review
                analysis = analyzer.analyze_text(review.text)

                # Combine review data with analysis
                review_dict = review.model_dump()
                review_dict.update(analysis)
                reviews.append(review_dict)
            except Exception as e:
                logger.error(f"Error processing row: {str(e)}")
                continue

        logger.info(f"Processed {len(reviews)} reviews from CSV")
        return reviews
    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scrape", response_model=List[ReviewResponse])
async def scrape_data(source: str, query: str = None, app_id: str = None, limit: int = 50):
    try:
        # Validate parameters
        if source not in ["twitter", "playstore"]:
            raise ValueError("Source must be 'twitter' or 'playstore'")

        if source == "twitter" and not query:
            raise ValueError("Query parameter is required for Twitter scraping")

        if source == "playstore" and not app_id:
            raise ValueError("App ID parameter is required for Play Store scraping")

        # Scrape data
        scraped_data = scraper.scrape(source, query, app_id, limit)

        # Analyze each review
        analyzed_reviews = []
        for review in scraped_data:
            analysis = analyzer.analyze_text(review['text'])
            review.update(analysis)
            analyzed_reviews.append(review)

        return analyzed_reviews

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=List[ReviewResponse])
async def analyze_reviews(reviews: List[ReviewCreate]):
    try:
        analyzed_reviews = []
        for review in reviews:
            # Clean and analyze the text
            analysis = analyzer.analyze_text(review.text)

            # Combine review data with analysis
            review_dict = review.model_dump()
            review_dict.update(analysis)
            analyzed_reviews.append(review_dict)

        return analyzed_reviews

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary", response_model=SummaryResponse)
async def get_summary(reviews: List[ReviewResponse]):
    try:
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")

        return analyzer.generate_summary(reviews)

    except Exception as e:
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