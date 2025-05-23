from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import core modules
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "app")
if os.path.exists(app_dir) and current_dir not in sys.path:
    sys.path.append(current_dir)
    logger.info(f"Added {current_dir} to sys.path")

try:
    from app.api.routes import router as api_router
    from app.api.timing_routes import router as timing_router
    from app.api.history_routes import router as history_router
    from app.api.sentiment_routes import router as sentiment_router
    from app.api.weekly_routes import router as weekly_router
    from app.api.websocket_routes import router as websocket_router
    from app.utils.exceptions import ReviewSystemException
    from app.mongodb import init_mongodb
    logger.info("Successfully imported app modules")
except ModuleNotFoundError as e:
    logger.error(f"Error importing modules: {str(e)}")
    raise

# Import Gemini routes
try:
    from app.api.gemini_routes import router as gemini_router
    logger.info("Successfully imported Gemini routes from app.api")
    GEMINI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Gemini routes could not be imported: {str(e)}. Gemini API will be disabled.")
    GEMINI_AVAILABLE = False

# Import MongoDB
try:
    from app.mongodb import get_client
    logger.info("Successfully imported MongoDB client from app.mongodb")

    # Set development mode for testing without MongoDB
    if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
        logger.warning("Running in DEVELOPMENT_MODE - MongoDB connection errors will be handled gracefully")
        os.environ["DEVELOPMENT_MODE"] = "true"

    # Test MongoDB connection
    client = get_client()
    client.admin.command('ping')
    MONGODB_AVAILABLE = True
    logger.info("MongoDB connection successful")
except Exception as e:
    if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
        logger.warning(f"MongoDB connection failed: {str(e)}. Running with limited functionality in development mode.")
        MONGODB_AVAILABLE = False
    else:
        logger.error(f"MongoDB connection failed: {str(e)}. Set DEVELOPMENT_MODE=true to run with limited functionality.")
        # In production, we still want to fail if MongoDB is not available
        raise

# Define lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize MongoDB
    logger.info("Starting up the application...")
    try:
        await init_mongodb()
    except Exception as e:
        if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
            logger.warning(f"MongoDB initialization failed: {str(e)}. Running with limited functionality in development mode.")
        else:
            logger.error(f"MongoDB initialization failed: {str(e)}. Set DEVELOPMENT_MODE=true to run with limited functionality.")
            raise
    yield
    # Shutdown: nothing to do here
    logger.info("Shutting down the application...")

# Set database availability
DATABASE_AVAILABLE = MONGODB_AVAILABLE

# Try to import advanced routes
try:
    from app.api.advanced_routes import router as advanced_router
    ADVANCED_ROUTES_AVAILABLE = True
except ImportError:
    logger.warning("Advanced routes could not be imported. Advanced analysis will be disabled.")
    ADVANCED_ROUTES_AVAILABLE = False

# Import auth router
try:
    # Use MongoDB auth router
    from app.auth.mongo_router import router as auth_router
    logger.info("Using MongoDB authentication")
    AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Auth router could not be imported: {str(e)}. Authentication will be disabled.")
    AUTH_AVAILABLE = False

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

# Create FastAPI app with lifespan
app = FastAPI(
    title="Product Pulse API",
    description="AI-Powered Feedback Analysis for Product Managers",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for both development and production
frontend_url = os.getenv("FRONTEND_URL", "")
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:3004",
    "http://127.0.0.1:5173"
]

# Add production URLs if available
if frontend_url:
    origins.append(frontend_url)
    # Also add https version
    if frontend_url.startswith("http://"):
        origins.append(frontend_url.replace("http://", "https://"))

logger.info(f"Configuring CORS with allowed origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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

# Include weekly routes
logger.info("Including weekly routes")
app.include_router(weekly_router, prefix="/api")

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

# Include WebSocket routes
logger.info("Including WebSocket routes")
app.include_router(websocket_router)

# Health check endpoint removed for production

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

    if MONGODB_AVAILABLE:
        features.append("MongoDB Atlas Database Storage")

    return {
        "message": "Welcome to the AI-Powered Feedback Analyzer API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "features": features,
        "status": "Some features may be limited based on installed packages"
    }