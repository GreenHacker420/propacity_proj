from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import core modules
from app.api.routes import router as api_router
from app.api.timing_routes import router as timing_router
from app.api.history_routes import router as history_router
from app.api.sentiment_routes import router as sentiment_router
from app.utils.exceptions import ReviewSystemException

# Try to import Gemini routes
try:
    from app.api.gemini_routes import router as gemini_router
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Gemini routes could not be imported. Gemini API will be disabled.")
    GEMINI_AVAILABLE = False

# Try to import SQLite database
try:
    from app.database import engine, Base
    SQLITE_AVAILABLE = True
except ImportError:
    logger.warning("SQLite database module could not be imported. SQLite functionality will be disabled.")
    SQLITE_AVAILABLE = False

# Try to import MongoDB
try:
    from app.mongodb import get_client
    # Test MongoDB connection
    client = get_client()
    client.admin.command('ping')
    MONGODB_AVAILABLE = True
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {str(e)}. MongoDB functionality will be disabled.")
    MONGODB_AVAILABLE = False

# Set overall database availability
DATABASE_AVAILABLE = SQLITE_AVAILABLE or MONGODB_AVAILABLE

# Try to import advanced routes
try:
    from app.api.advanced_routes import router as advanced_router
    ADVANCED_ROUTES_AVAILABLE = True
except ImportError:
    logger.warning("Advanced routes could not be imported. Advanced analysis will be disabled.")
    ADVANCED_ROUTES_AVAILABLE = False

# Try to import auth router
try:
    from app.auth.router import router as auth_router
    AUTH_AVAILABLE = True
except ImportError:
    logger.warning("Auth router could not be imported. Authentication will be disabled.")
    AUTH_AVAILABLE = False

# Create database tables if SQLite is available
if SQLITE_AVAILABLE:
    try:
        logger.info("Creating SQLite database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating SQLite database tables: {str(e)}")
        logger.warning("Application will run with limited SQLite functionality")
else:
    logger.warning("Skipping SQLite database table creation as SQLite is not available")

# Log MongoDB status
if MONGODB_AVAILABLE:
    logger.info("MongoDB is available and connected")
    # Check if collections exist
    db = get_client()["product_reviews"]
    collections = db.list_collection_names()

    if collections:
        logger.info(f"MongoDB collections: {collections}")
        # Count documents in each collection
        for collection in collections:
            count = db[collection].count_documents({})
            logger.info(f"Collection '{collection}' has {count} documents")
    else:
        logger.warning("No MongoDB collections found. You may need to run the migration script.")
        logger.info("Creating empty MongoDB collections...")
        # Create empty collections
        db.create_collection("users")
        db.create_collection("reviews")
        db.create_collection("keywords")
        db.create_collection("analysis_history")
        db.create_collection("processing_times")
        logger.info("Empty MongoDB collections created")
else:
    logger.warning("MongoDB is not available")

app = FastAPI(
    title="AI-Powered Feedback Analyzer",
    description="Advanced API for analyzing product reviews and generating actionable insights using AI",
    version="2.0.0"
)

# Configure CORS
origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
logger.info(f"Configuring CORS with allowed origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(ReviewSystemException)
async def review_system_exception_handler(_: Request, exc: ReviewSystemException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Include API routes
app.include_router(api_router, prefix="/api")

# Include timing routes
logger.info("Including timing routes")
app.include_router(timing_router, prefix="/api")

# Include history routes
logger.info("Including history routes")
app.include_router(history_router, prefix="/api")

# Include sentiment routes
logger.info("Including advanced sentiment analysis routes")
app.include_router(sentiment_router, prefix="/api")

# Include advanced routes if available
if ADVANCED_ROUTES_AVAILABLE:
    logger.info("Including advanced analysis routes")
    app.include_router(advanced_router, prefix="/api")
else:
    logger.warning("Advanced analysis routes are not available")

# Include Gemini routes if available
if GEMINI_AVAILABLE:
    logger.info("Including Gemini API routes")
    app.include_router(gemini_router, prefix="/api")
else:
    logger.warning("Gemini API routes are not available")

# Include auth routes if available
if AUTH_AVAILABLE:
    logger.info("Including authentication routes")
    app.include_router(auth_router, prefix="/api")
else:
    logger.warning("Authentication routes are not available")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    # Determine available features based on what's installed
    features = ["Basic Sentiment Analysis", "CSV Upload and Processing"]

    if ADVANCED_ROUTES_AVAILABLE:
        features.extend([
            "Advanced NLP with Named Entity Recognition",
            "Topic Modeling with LDA",
            "Aspect-Based Sentiment Analysis",
            "Emotion Detection",
            "Trend Analysis and Time Series Visualization",
            "User Feedback Clustering",
            "Automated Actionable Insights"
        ])

    if GEMINI_AVAILABLE:
        features.extend([
            "Google Gemini API Integration",
            "Fast Batch Processing with Gemini",
            "Advanced Insight Extraction with Gemini"
        ])

    if 'langid' in globals() or 'LANGID_AVAILABLE' in globals():
        features.append("Multi-language Support")

    if AUTH_AVAILABLE:
        features.append("User Authentication")

    if SQLITE_AVAILABLE:
        features.append("SQLite Database Storage")

    if MONGODB_AVAILABLE:
        features.append("MongoDB Atlas Database Storage")

    return {
        "message": "Welcome to the AI-Powered Feedback Analyzer API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "features": features,
        "status": "Some features may be limited based on installed packages"
    }