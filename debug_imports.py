#!/usr/bin/env python
"""
Debug script to help diagnose import issues in the deployment environment.
"""

import os
import sys
import logging
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def debug_imports():
    """Debug imports by checking various paths and attempting imports."""
    logger.info("Starting import debugging")
    
    # Print current working directory and Python path
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Check if key directories exist
    backend_dir = os.path.join(os.getcwd(), "backend")
    app_dir = os.path.join(backend_dir, "app")
    api_dir = os.path.join(app_dir, "api")
    
    logger.info(f"Backend directory exists: {os.path.exists(backend_dir)}")
    logger.info(f"App directory exists: {os.path.exists(app_dir)}")
    logger.info(f"API directory exists: {os.path.exists(api_dir)}")
    
    # List files in key directories
    if os.path.exists(backend_dir):
        logger.info(f"Files in backend directory: {os.listdir(backend_dir)}")
    
    if os.path.exists(app_dir):
        logger.info(f"Files in app directory: {os.listdir(app_dir)}")
    
    if os.path.exists(api_dir):
        logger.info(f"Files in api directory: {os.listdir(api_dir)}")
    
    # Try different import paths
    import_paths = [
        "backend.main",
        "main",
        "backend.app.api.routes",
        "app.api.routes",
        "api.routes",
        "routes"
    ]
    
    for path in import_paths:
        try:
            logger.info(f"Trying to import {path}")
            module = importlib.import_module(path)
            logger.info(f"Successfully imported {path}")
            logger.info(f"Module details: {module}")
        except Exception as e:
            logger.error(f"Failed to import {path}: {e}")
    
    logger.info("Import debugging complete")

if __name__ == "__main__":
    debug_imports()
