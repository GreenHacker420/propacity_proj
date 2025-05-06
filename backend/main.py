from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import importlib.util

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

# Try to import database
try:
    from app.database import engine, Base
    DATABASE_AVAILABLE = True
except ImportError:
    logger.warning("Database module could not be imported. Database functionality will be disabled.")
    DATABASE_AVAILABLE = False

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

# Create database tables if available
if DATABASE_AVAILABLE:
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        logger.warning("Application will run with limited database functionality")
else:
    logger.warning("Skipping database table creation as database is not available")

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
async def review_system_exception_handler(request: Request, exc: ReviewSystemException):
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

    if 'langid' in globals() or 'LANGID_AVAILABLE' in globals():
        features.append("Multi-language Support")

    if AUTH_AVAILABLE:
        features.append("User Authentication")

    if DATABASE_AVAILABLE:
        features.append("Database Storage")

    return {
        "message": "Welcome to the AI-Powered Feedback Analyzer API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "features": features,
        "status": "Some features may be limited based on installed packages"
    }