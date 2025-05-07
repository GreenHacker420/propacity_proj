#!/bin/bash
set -e

echo "Starting build process..."

# Check for Node.js and npm
echo "Checking for Node.js and npm..."
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm."
    exit 1
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# Check for Python
echo "Checking for Python..."
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python."
    exit 1
fi

echo "Python version: $(python --version)"

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Download NLTK resources
echo "Downloading NLTK resources..."
python download_nltk_resources.py

# Install frontend dependencies and build
echo "Installing frontend dependencies and building..."
cd ../frontend
npm install
npm run build

echo "Build process completed successfully!"
