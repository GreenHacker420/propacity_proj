#!/usr/bin/env python
"""
Script to fix Python path issues in the deployment environment.
This script should be imported at the beginning of serve.py.
"""

import os
import sys
import logging
import importlib.util
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def check_and_install_hf_xet():
    """Check if hf_xet is installed and install it if not."""
    try:
        # Check if hf_xet is installed
        if importlib.util.find_spec("hf_xet") is None:
            logger.warning("hf_xet package not found. Attempting to install it...")
            try:
                # Try to install hf_xet
                subprocess.check_call([sys.executable, "-m", "pip", "install", "hf_xet"])
                logger.info("Successfully installed hf_xet package")

                # Also ensure huggingface_hub with hf_xet is installed
                subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub[hf_xet]", "--upgrade"])
                logger.info("Successfully upgraded huggingface_hub with hf_xet support")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install hf_xet: {e}")
                logger.warning("Continuing without hf_xet. Model downloads may be slower.")
        else:
            logger.info("hf_xet package is already installed")
    except Exception as e:
        logger.error(f"Error checking/installing hf_xet: {e}")
        logger.warning("Continuing without checking for hf_xet")

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

    # Check and install hf_xet if needed
    check_and_install_hf_xet()

# Run the function when the module is imported
fix_python_path()
