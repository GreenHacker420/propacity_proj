# Product Review Analyzer

A full-stack web application that analyzes user feedback (tweets, reviews) and provides a weekly summary for product managers.

## Features

- Upload CSV files with user feedback
- Scrape real-time feedback from Twitter and Google Play Store
- Analyze sentiment and categorize feedback into:
  - Pain points
  - Feature requests
  - Positive feedback
- Extract keywords from feedback
- Generate summaries with top insights
- Download PDF reports with actionable priorities for product managers

## Tech Stack

### Backend
- FastAPI (Python)
- Hugging Face Transformers for sentiment analysis
- KeyBERT for keyword extraction
- snscrape for Twitter data
- google-play-scraper for Play Store data
- WeasyPrint for PDF generation

### Frontend
- React
- Tailwind CSS
- Headless UI components
- Axios for API calls

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

3. Run the backend server:
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

- `POST /api/upload` - Upload and analyze a CSV file
- `GET /api/scrape` - Scrape and analyze data from Twitter or Play Store
- `POST /api/analyze` - Analyze a list of reviews
- `POST /api/summary` - Generate a summary from analyzed reviews
- `POST /api/summary/pdf` - Generate a PDF report

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