from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.utils.exceptions import ReviewSystemException

app = FastAPI(
    title="Product Review Analyzer",
    description="API for analyzing product reviews and generating insights",
    version="1.0.0"
)

# Configure CORS
origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
print(f"Configuring CORS with allowed origins: {origins}")
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Welcome to Product Review Analyzer API"}