# Installation Guide

This guide provides step-by-step instructions for installing and setting up the Product Review Analyzer.

## Prerequisites

Before installing, ensure you have:

1. **Python 3.11**: The backend requires Python 3.11 for compatibility with all dependencies
2. **Node.js 16+**: Required for the frontend
3. **MongoDB Atlas Account**: For database storage
4. **Google Gemini API Key**: For advanced AI analysis

## Backend Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/product-review-analyzer.git
cd product-review-analyzer
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key_for_jwt
DEBUG=False
```

### Step 4: Initialize the Database

The application will automatically create the necessary collections in MongoDB when it first starts.

### Step 5: Start the Backend Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uvicorn app.main:app --reload
```

## Frontend Installation

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

### Step 2: Configure Environment Variables

Create a `.env` file in the `frontend` directory:

```
REACT_APP_API_URL=http://localhost:8000/api
```

### Step 3: Build the Frontend (Production)

```bash
npm run build
```

### Step 4: Start the Development Server

For development:

```bash
npm start
```

## Docker Installation

If you prefer using Docker, follow these steps:

### Step 1: Configure Environment Variables

Create a `.env` file in the project root:

```
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key_for_jwt
DEBUG=False
```

### Step 2: Build and Start Containers

```bash
docker-compose build
docker-compose up -d
```

## Verifying Installation

### Backend Verification

1. Access the API documentation at `http://localhost:8000/docs`
2. Verify that all endpoints are listed
3. Test the health check endpoint at `http://localhost:8000/api/health`

### Frontend Verification

1. Access the frontend at `http://localhost:3000`
2. Verify that you can log in
3. Test uploading a small CSV file
4. Check that analysis results are displayed correctly

## Common Installation Issues

### Python Version Compatibility

The application requires Python 3.11 for compatibility with all dependencies. If you encounter errors like:

```
ERROR: Could not find a version that satisfies the requirement spacy==3.x.x
```

Ensure you're using Python 3.11:

```bash
python --version
```

### MongoDB Connection Issues

If you see errors connecting to MongoDB:

1. Verify your connection string is correct
2. Ensure your IP address is whitelisted in MongoDB Atlas
3. Check that the database user has the correct permissions

### Gemini API Key Issues

If the Gemini API integration isn't working:

1. Verify your API key is correct
2. Check that the API key has the necessary permissions
3. Ensure you have sufficient quota for your usage

## Next Steps

After installation:

1. Create a user account
2. Upload your first CSV file for analysis
3. Explore the various features of the application
4. Check the [User Guide](../features/user-guide.md) for detailed usage instructions
