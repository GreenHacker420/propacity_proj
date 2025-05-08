#!/bin/bash
# Main build script for AWS deployment

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Building Product Review Analyzer for AWS deployment ===${NC}"

# Check if we're in the project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error:${NC} This script must be run from the project root directory"
    echo "Current directory: $(pwd)"
    echo "Please change to the project root directory and try again"
    exit 1
fi

# Create production .env file for backend
echo -e "\n${GREEN}=== Creating production .env file for backend ===${NC}"
if [ ! -f "backend/.env.production" ]; then
    echo "Creating backend/.env.production from template..."
    cat > backend/.env.production << EOL
# Production environment variables
MONGODB_URI=your_mongodb_uri
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_MODEL=models/gemini-2.0-flash
PORT=8000
HOST=0.0.0.0
DEVELOPMENT_MODE=false
EOL
    echo "Created backend/.env.production"
    echo -e "${YELLOW}Warning:${NC} Please edit backend/.env.production to set your actual MongoDB URI and Gemini API key"
else
    echo "backend/.env.production already exists, skipping creation"
fi

# Create production .env file for frontend
echo -e "\n${GREEN}=== Creating production .env file for frontend ===${NC}"
cat > frontend/.env.production << EOL
VITE_API_URL=/api
EOL
echo "Created frontend/.env.production"

# Build the frontend
echo -e "\n${GREEN}=== Building frontend ===${NC}"
if [ -f "scripts/aws/build_frontend_aws.sh" ]; then
    chmod +x scripts/aws/build_frontend_aws.sh
    ./scripts/aws/build_frontend_aws.sh
else
    echo -e "${YELLOW}Warning:${NC} build_frontend_aws.sh not found, using standard build process"
    cd frontend
    npm install
    NODE_ENV=production npm run build
    cd ..
fi

# Check if serve.py exists
echo -e "\n${GREEN}=== Checking for serve.py ===${NC}"
if [ ! -f "serve.py" ]; then
    echo "Creating serve.py..."
    cat > serve.py << EOL
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
EOL
    chmod +x serve.py
    echo "Created serve.py"
else
    echo "serve.py already exists, skipping creation"
fi

# Create start.sh script
echo -e "\n${GREEN}=== Creating start.sh script ===${NC}"
cat > start.sh << EOL
#!/bin/bash
# Startup script for the application in the production environment

# Print environment information
echo "Current directory: \$(pwd)"
echo "Python version: \$(python --version)"
echo "Node.js version: \$(node --version)"
echo "npm version: \$(npm --version)"

# Set up Python path
export PYTHONPATH=\$PYTHONPATH:\$(pwd):\$(pwd)/backend

# Set production mode
export DEVELOPMENT_MODE=false

# Start the application
echo "Starting the application..."
python serve.py
EOL
chmod +x start.sh
echo "Created start.sh"

echo -e "\n${GREEN}=== Build completed successfully ===${NC}"
echo "You can now deploy the application to AWS using:"
echo "./scripts/aws/deploy_aws.sh -h <EC2_HOST> -k <PEM_FILE>"
