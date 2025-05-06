# Product Review Analyzer

A powerful AI-driven application for analyzing product reviews, user feedback, and GitHub issues to generate actionable insights for product managers and development teams.

## Features

- **Upload CSV files** with user feedback
- **Scrape real-time feedback** from Google Play Store
- **Analyze GitHub repositories** for issues and discussions
- **Advanced sentiment analysis** with:
  - Context-aware sentiment detection
  - Aspect-based sentiment analysis
  - Google Gemini API integration for faster processing
- **Categorize feedback** into:
  - Pain points
  - Feature requests
  - Positive feedback
- **Extract keywords** from feedback
- **Generate summaries** with top insights
- **Download PDF reports** with actionable priorities for product managers
- **Track analysis history** and view past results
- **Dynamic processing time estimation** based on historical data
- **Batch processing** with Gemini API for improved performance
- **Multi-language support** for analyzing reviews in different languages
- **MongoDB Atlas integration** for scalable data storage

## Tech Stack

### Backend
- **FastAPI** (Python)
- **MongoDB Atlas** for database storage
- **Hugging Face Transformers** for sentiment analysis
- **Google Gemini API** for advanced text processing (using Gemini 2.0 Flash model)
- **NLTK** and **spaCy** for NLP tasks
- **PyMongo** for MongoDB integration
- **google-play-scraper** for Play Store data
- **WeasyPrint** for PDF generation

### Frontend
- **React**
- **Tailwind CSS**
- **Headless UI** components
- **Framer Motion** for animations
- **Axios** for API calls
- **React Dropzone** for file uploads
- **React Markdown** for rendering markdown content

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
│   ├── download_nltk_resources.py  # NLTK setup script
│   ├── requirements.txt  # Python dependencies
│   └── main.py          # FastAPI application entry
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API services
│   │   ├── App.jsx       # Main application component
│   │   ├── index.css     # Tailwind CSS styles
│   │   └── main.jsx      # Entry point
│   ├── tailwind.config.js # Tailwind configuration
│   └── package.json      # Node dependencies
├── package.json          # Root package.json with scripts
└── README.md             # Project documentation
```

## Prerequisites

- **Node.js** (v16+)
- **Python** (v3.9+, avoid 3.13 due to compatibility issues)
- **MongoDB Atlas** account
- **Google Gemini API** key (for enhanced analysis)

## Setup Instructions

### Complete Setup (Backend and Frontend)

1. Install all dependencies at once:
```bash
npm run install:all
```

2. Start both backend and frontend:
```bash
npm run dev
```

### Manual Setup

#### Backend Setup

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

3. Download NLTK resources:
```bash
python download_nltk_resources.py
```

4. Set up environment variables:
```bash
# Copy the example .env file
cp .env.mongodb.example .env

# Edit the .env file to add your MongoDB URI and Gemini API key
# You can get a Gemini API key from https://ai.google.dev/
```

5. Run the backend server:
```bash
uvicorn main:app --reload
```

#### Frontend Setup

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
- `GET /api/scrape` - Scrape and analyze data from Google Play Store
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

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user information

## Environment Variables

### Required Variables
- `MONGODB_URI` - MongoDB Atlas connection string
- `SECRET_KEY` - Secret key for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration time in minutes

### Optional Variables
- `GEMINI_API_KEY` - Google Gemini API key for enhanced analysis
- `GEMINI_MODEL` - Gemini model to use (default: gemini-1.5-pro)
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)

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
"The app keeps crashing whenever I try to upload photos",user1,2023-04-29,2
"Would love to have dark mode in the next update!",user2,2023-04-30,4
"Everything works flawlessly. Great job!",user3,2023-04-30,5
```

## MongoDB Collections

The application uses the following MongoDB collections:
- `users` - User accounts and authentication information
- `reviews` - Analyzed reviews and feedback
- `keywords` - Extracted keywords and their frequencies
- `analysis_history` - History of analysis operations
- `processing_times` - Processing time records for estimation

## License

MIT