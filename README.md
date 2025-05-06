# Product Review Analyzer

A full-stack web application that analyzes user feedback (tweets, reviews) and provides a weekly summary for product managers.

## Features

- Upload CSV files with user feedback
- Scrape real-time feedback from Twitter and Google Play Store
- Analyze GitHub repositories for issues and discussions
- Advanced sentiment analysis with:
  - Context-aware sentiment detection
  - Sarcasm and irony detection
  - Aspect-based sentiment analysis
  - Google Gemini API integration for faster processing
- Categorize feedback into:
  - Pain points
  - Feature requests
  - Positive feedback
- Extract keywords from feedback
- Generate summaries with top insights
- Download PDF reports with actionable priorities for product managers
- Track analysis history and view past results
- Dynamic processing time estimation based on historical data
- Batch processing with Gemini API for improved performance

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy for database ORM
- Hugging Face Transformers for sentiment analysis
- Google Gemini API for advanced text processing
- NLTK and VADER for rule-based sentiment analysis
- spaCy for NLP tasks and context analysis
- KeyBERT for keyword extraction
- snscrape for Twitter data
- google-play-scraper for Play Store data
- WeasyPrint for PDF generation

### Frontend
- React
- Tailwind CSS
- Headless UI components
- Framer Motion for animations
- Axios for API calls
- Chart.js for data visualization

## Project Structure

```
product-review-analyzer/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints and models
│   │   ├── auth/         # Authentication
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic (scraper, analyzer)
│   │   └── utils/        # Utilities and exceptions
│   ├── mock_reviews.csv  # Sample data for testing
│   ├── requirements.txt  # Python dependencies
│   └── main.py          # FastAPI application entry
├── frontend/             # React frontend
│   ├── src/
│   │   ├── App.jsx      # Main application component
│   │   ├── index.css    # Tailwind CSS styles
│   │   └── main.jsx     # Entry point
│   ├── tailwind.config.js # Tailwind configuration
│   └── package.json     # Node dependencies
└── README.md            # Project documentation
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy the example .env file
cp .env.example .env

# Edit the .env file to add your Gemini API key
# You can get a Gemini API key from https://ai.google.dev/
```

4. Run the backend server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## API Endpoints

### Core Endpoints
- `POST /api/upload` - Upload and analyze a CSV file
- `GET /api/scrape` - Scrape and analyze data from Twitter or Play Store
- `POST /api/analyze` - Analyze a list of reviews
- `POST /api/summary` - Generate a summary from analyzed reviews
- `POST /api/summary/pdf` - Generate a PDF report

### Advanced Sentiment Analysis
- `POST /api/sentiment/analyze` - Analyze sentiment of a single text with advanced features
- `POST /api/sentiment/batch` - Analyze sentiment of multiple texts

### Gemini API Integration
- `POST /api/gemini/sentiment` - Analyze sentiment using Google's Gemini API
- `POST /api/gemini/batch` - Batch process multiple texts with Gemini
- `POST /api/gemini/insights` - Extract insights from reviews using Gemini

### History Tracking
- `POST /api/history` - Record an analysis in the history
- `GET /api/history` - Get analysis history
- `GET /api/history/{analysis_id}` - Get a specific analysis by ID
- `DELETE /api/history/{analysis_id}` - Delete an analysis history record

### Processing Time Tracking
- `POST /api/timing/record` - Record processing time for an operation
- `GET /api/timing/estimate/{operation}` - Get estimated processing time
- `GET /api/timing/history` - Get processing time history

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive API documentation.

## CSV Format

The CSV file should contain the following columns:
- `text` (required) - The feedback content
- `username` (optional) - The user who provided the feedback
- `timestamp` (optional) - When the feedback was provided
- `rating` (optional) - A numerical rating (1-5)

Example:
```csv
text,username,timestamp,rating
"The app keeps crashing whenever I try to upload photos",user1,2025-04-29,2
"Would love to have dark mode in the next update!",user2,2025-04-30,4
"Everything works flawlessly. Great job!",user3,2025-04-30,5
```

## License

MIT