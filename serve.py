#!/usr/bin/env python
"""
Script to serve both the backend API and frontend static files.
This is used in production to serve the entire application from a single process.
"""

# Import fix_path.py to fix Python path issues
import fix_path

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
try:
    # First try the direct import (for local development)
    from backend.main import app as api_app
    logger.info("Successfully imported backend.main")
except ModuleNotFoundError:
    # If that fails, try to import using a different path (for deployment)
    import sys
    logger.info(f"Current sys.path: {sys.path}")

    # Add the backend directory to the path
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
        logger.info(f"Added {backend_dir} to sys.path")

    try:
        # Try importing from the main module directly
        from main import app as api_app
        logger.info("Successfully imported main")
    except ModuleNotFoundError as e:
        logger.error(f"Failed to import main: {e}")
        raise

# Define the path to the frontend build directory
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

# Check if the frontend build directory exists
if not os.path.exists(FRONTEND_DIR):
    logger.warning(f"Frontend build directory not found at {FRONTEND_DIR}")
    logger.warning("Checking if we need to create the directory...")

    # Check if the frontend source directory exists
    frontend_src_dir = os.path.join(os.path.dirname(__file__), "frontend", "src")
    if os.path.exists(frontend_src_dir):
        logger.warning("Frontend source directory exists, but build directory does not.")
        logger.warning("This might indicate that the frontend has not been built yet.")
        logger.warning("Only the API will be served")
    else:
        logger.warning("Frontend source directory not found either.")
        logger.warning("This might indicate that the frontend code is not available.")
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
    # Run the debug script first
    try:
        import debug_imports
        debug_imports.debug_imports()
    except Exception as e:
        logger.error(f"Error running debug script: {e}")

    # Get the port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))

    # Run the server
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
