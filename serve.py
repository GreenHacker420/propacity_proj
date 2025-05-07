#!/usr/bin/env python
"""
Script to serve both the backend API and frontend static files.
This is used in production to serve the entire application from a single process.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the main FastAPI application
from backend.main import app as api_app

# Define the path to the frontend build directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Check if the frontend build directory exists
if not os.path.exists(FRONTEND_DIR):
    logger.warning(f"Frontend build directory not found at {FRONTEND_DIR}")
    logger.warning("Only the API will be served")
    HAS_FRONTEND = False
else:
    logger.info(f"Frontend build directory found at {FRONTEND_DIR}")
    HAS_FRONTEND = True

# Create a new FastAPI application that will serve both the API and frontend
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use the lifespan from the API app
    async with api_app.router.lifespan_context({}):
        yield

app = FastAPI(lifespan=lifespan)

# Mount the API app at /api
app.mount("/api", api_app)

# Serve frontend static files if available
if HAS_FRONTEND:
    # Mount the static files directory
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    
    # Serve the index.html for all other routes
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # For the root path or any other path, serve the index.html
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return {"error": "Frontend not built. Please run 'npm run build' in the frontend directory."}

if __name__ == "__main__":
    # Get the port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
