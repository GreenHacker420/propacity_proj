#!/bin/bash
# Startup script for the application in the production environment

# Print environment information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/backend

# Set production mode
export DEVELOPMENT_MODE=false

# Start the application
echo "Starting the application..."
python serve.py
