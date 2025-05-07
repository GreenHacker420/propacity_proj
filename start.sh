#!/bin/bash
# Startup script for the application in the deployment environment

# Print environment information
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# List key directories
echo "Listing key directories:"
echo "Root directory:"
ls -la
echo "Backend directory:"
ls -la backend
echo "Backend app directory:"
ls -la backend/app
echo "Frontend directory:"
ls -la frontend

# Set up Python path
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/backend

# Print Python path
echo "Python path: $PYTHONPATH"

# Start the application
echo "Starting the application..."
python serve.py
