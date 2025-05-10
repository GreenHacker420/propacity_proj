# Product Review Analyzer

A powerful AI-driven application for analyzing product reviews, user feedback, and GitHub issues to generate actionable insights for product managers and development teams.

## Features

- **Upload CSV files** with user feedback
- **Scrape real-time feedback** from Google Play Store
- **Generate Twitter data** using Gemini API with fallback mechanisms
- **Analyze GitHub repositories** for issues and discussions
- **Advanced sentiment analysis** with:
  - Context-aware sentiment detection
  - Aspect-based sentiment analysis
  - Local processing for sentiment analysis to avoid API rate limits
  - Parallel processing for improved performance
- **Categorize feedback** into:
  - Pain points
  - Feature requests
  - Positive feedback
- **Extract keywords** from feedback
- **Generate summaries** with top insights
- **Weekly summaries** for product prioritization
- **Download PDF reports** with actionable priorities for product managers
- **Track analysis history** and view past results with full summaries
- **Dynamic processing time estimation** based on historical data
- **Real-time progress updates** via WebSockets
- **Advanced Gemini API integration** with:
  - Local processing for sentiment analysis to avoid API rate limits
  - Gemini API for insight extraction and summary generation
  - Intelligent batch processing for optimal performance
  - Adaptive request throttling to prevent rate limits
  - Robust JSON parsing with multiple fallback mechanisms
  - Multi-level caching system for faster responses
  - Circuit breaker pattern for graceful degradation
- **Multi-language support** for analyzing reviews in different languages
- **MongoDB Atlas integration** for scalable data storage
- **Optimized batch processing** with dynamic batch sizing and RAM usage optimization

## Tech Stack

### Backend
- **FastAPI** (Python)
- **WebSockets** for real-time progress updates
- **MongoDB Atlas** for database storage
- **Hugging Face Transformers** for sentiment analysis
- **Google Gemini API** for advanced text processing (using Gemini 2.0 Flash model)
- **NLTK** and **spaCy** for NLP tasks
- **PyMongo** for MongoDB integration
- **google-play-scraper** for Play Store data
- **Gemini API** for Twitter data generation
- **WeasyPrint** for PDF generation
- **Parallel processing** for improved performance

### Frontend
- **React**
- **Tailwind CSS**
- **Headless UI** components
- **Framer Motion** for animations
- **Axios** for API calls
- **WebSocket** for real-time updates
- **React Dropzone** for file uploads
- **React Markdown** for rendering markdown content
- **Recharts** for data visualization

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
│   ├── requirements.aws.txt  # AWS-specific dependencies
│   └── main.py           # FastAPI application entry
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── config/       # Configuration files
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API services
│   │   ├── App.jsx       # Main application component
│   │   ├── index.css     # Tailwind CSS styles
│   │   └── main.jsx      # Entry point
│   ├── tailwind.config.js # Tailwind configuration
│   ├── vite.config.js    # Vite configuration
│   └── package.json      # Node dependencies
├── docs/                 # Documentation
│   ├── api/              # API documentation
│   ├── deployment/       # Deployment guides
│   │   ├── aws.md        # AWS deployment guide
│   │   └── railway.md    # Railway deployment guide
│   ├── features/         # Feature documentation
│   └── troubleshooting/  # Troubleshooting guides
├── scripts/              # Deployment and setup scripts
│   ├── aws/              # AWS deployment scripts
│   │   ├── build.sh      # AWS build script
│   │   ├── deploy_aws.sh # AWS deployment script
│   │   ├── setup_aws.sh  # AWS setup script
│   │   ├── install_aws_deps.sh # AWS dependencies installer
│   │   └── build_frontend_aws.sh # AWS frontend build script
│   └── build.sh          # Production build script
├── serve.py              # Production server script
├── start.sh              # Production startup script
├── package.json          # Root package.json with scripts
└── README.md             # Project documentation
```

## Prerequisites

- **Node.js** (v16+)
- **Python** (v3.11 recommended, avoid 3.13 due to compatibility issues)
- **MongoDB Atlas** account
- **Google Gemini API** key (for enhanced analysis)
- **AWS Account** (for AWS deployment)

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

### AWS Deployment

For production deployment on AWS:

1. Configure your AWS credentials and EC2 instance
2. Build the application for production:
```bash
# Make the build script executable
chmod +x scripts/aws/build.sh

# Run the build script
./scripts/aws/build.sh
```

3. Deploy to AWS:
```bash
# Make the deployment script executable
chmod +x scripts/aws/deploy_aws.sh

# Deploy to AWS
./scripts/aws/deploy_aws.sh -h <EC2_HOST> -k <PEM_FILE>
```

The deployment script will:
- Package your application
- Upload it to your EC2 instance
- Install all dependencies
- Configure Nginx as a reverse proxy
- Set up a systemd service for the application
- Start the application

For detailed AWS deployment instructions, see the [AWS Deployment Guide](docs/deployment/aws.md).

### Railway Deployment

For deployment on Railway:

1. Connect your GitHub repository to Railway
2. Configure the environment variables in Railway dashboard
3. Deploy the application

For detailed Railway deployment instructions, see the [Railway Deployment Guide](docs/deployment/railway.md).

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
- `GET /api/scrape` - Scrape and analyze data from Google Play Store or Twitter
- `POST /api/analyze` - Analyze a list of reviews
- `POST /api/summary` - Generate a summary from analyzed reviews
- `POST /api/summary/pdf` - Generate a PDF report
- `POST /api/summary/weekly` - Generate a weekly summary

### Advanced Sentiment Analysis
- `POST /api/sentiment/analyze` - Analyze sentiment of a single text with advanced features
- `POST /api/sentiment/batch` - Analyze sentiment of multiple texts

### Gemini API Integration
- `POST /api/gemini/sentiment` - Analyze sentiment using Google's Gemini API
- `POST /api/gemini/batch` - Batch process multiple texts with Gemini
- `POST /api/gemini/insights` - Extract insights from reviews using Gemini
- `GET /api/gemini/status` - Get detailed Gemini API status with performance metrics

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
- `GET /api/auth/user` - Get user information from token

### WebSocket Endpoints
- `ws://localhost:8000/ws/batch-progress` - Real-time batch processing progress updates
- `ws://localhost:8000/ws/sentiment-progress` - Real-time sentiment analysis progress updates

## Environment Variables

### Required Variables
- `MONGODB_URI` - MongoDB Atlas connection string (falls back to mock client in development mode)
- `SECRET_KEY` - Secret key for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration time in minutes

### Optional Variables
- `GEMINI_API_KEY` - Google Gemini API key for enhanced analysis
- `GEMINI_MODEL` - Gemini model to use (default: gemini-2.0-flash)
- `GEMINI_BATCH_SIZE` - Number of reviews to process in each Gemini API batch (default: 10)
- `GEMINI_SLOW_THRESHOLD` - Threshold in seconds to detect slow Gemini API processing (default: 5)
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
- `DEBUG` - Enable debug mode (default: False)
- `ENABLE_WEBSOCKETS` - Enable WebSocket support (default: True)
- `PARALLEL_PROCESSING` - Enable parallel processing (default: True)
- `MAX_WORKERS` - Maximum number of worker threads for parallel processing (default: 4)

### Production Variables
- `DEVELOPMENT_MODE` - Set to `false` for production environments (default: True)
  - When set to `true`, enables:
    - Mock MongoDB client when MongoDB is unavailable
    - Gemini API for Twitter data generation with fallbacks
    - Default timing estimates when MongoDB is unavailable
- `FRONTEND_URL` - URL of the frontend for CORS configuration (default: varies by environment)
- `LOG_LEVEL` - Logging level (default: INFO)
- `GUNICORN_WORKERS` - Number of Gunicorn workers for production (default: 4)
- `GUNICORN_TIMEOUT` - Timeout for Gunicorn workers in seconds (default: 120)

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive API documentation.

## Documentation

### Feature Documentation

- [Twitter Data Generation and Scraping](docs/features/twitter_scraping.md)
- [MongoDB Integration](docs/mongodb_integration.md)
- [Troubleshooting Common Issues](docs/troubleshooting/common_issues.md)

### Gemini API Integration

The application includes advanced integration with Google's Gemini API for enhanced text analysis capabilities. For detailed documentation, see [Gemini API Integration Documentation](docs/gemini_api_integration.md).

### Key Features

- **Intelligent Batch Processing**: Dynamically adjusts batch sizes based on review length
- **Multi-Level Caching System**: Implements LRU caching for faster responses
- **Adaptive Request Throttling**: Prevents rate limit errors by controlling request rates
- **Robust JSON Parsing**: Multiple fallback mechanisms for handling various response formats
- **Circuit Breaker Pattern**: Gracefully degrades to local processing when API is unavailable

### Performance Monitoring

The Gemini API integration includes comprehensive performance monitoring accessible through the `/api/gemini/status` endpoint, which provides detailed metrics on:

- API response times
- Cache efficiency
- Request throttling
- Error rates
- Circuit breaker status

For implementation details, troubleshooting tips, and best practices, refer to the [complete documentation](docs/gemini_api_integration.md).

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
- `analysis_history` - History of analysis operations with full summaries
- `processing_times` - Processing time records for estimation
- `weekly_summaries` - Weekly summaries for product prioritization
- `batch_progress` - Batch processing progress tracking

## License

MIT