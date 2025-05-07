#!/usr/bin/env python
"""
Script to fix Python path issues in the deployment environment.
This script should be imported at the beginning of serve.py.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def fix_python_path():
    """Fix Python path by adding necessary directories."""
    logger.info("Fixing Python path")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Current directory: {current_dir}")
    
    # Add the current directory to the path if not already there
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Added {current_dir} to sys.path")
    
    # Add the backend directory to the path
    backend_dir = os.path.join(current_dir, "backend")
    if os.path.exists(backend_dir) and backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
        logger.info(f"Added {backend_dir} to sys.path")
    
    # Log the updated Python path
    logger.info(f"Updated Python path: {sys.path}")

# Run the function when the module is imported
fix_python_path()
