# Deployment Guide

This guide provides instructions for deploying the Product Review Analyzer in various environments.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![React](https://img.shields.io/badge/React-Latest-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)
![AI](https://img.shields.io/badge/AI-Gemini_API-red)
![NLP](https://img.shields.io/badge/NLP-Sentiment_Analysis-yellow)
![Deployment](https://img.shields.io/badge/Deployment-AWS_EC2-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Deployment Options

- [Local Development](#local-development): For development and testing
- [Docker Deployment](#docker-deployment): For containerized deployment
- [AWS Deployment](aws.md): For production deployment on Amazon Web Services
- [Railway Deployment](#railway-deployment): For alternative cloud deployment

## Prerequisites

Before deploying the Product Review Analyzer, ensure you have:

1. **MongoDB Atlas Account**: For database storage
2. **Google Gemini API Key**: For advanced AI analysis
3. **Python 3.11**: For backend runtime
4. **Node.js**: For frontend development

## Local Development

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/product-review-analyzer.git
   cd product-review-analyzer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Set up environment variables:
   ```bash
   # Create a .env file in the backend directory
   echo "MONGODB_URI=your_mongodb_uri
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key
   " > backend/.env
   ```

5. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables:
   ```bash
   # Create a .env file in the frontend directory
   echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
   ```

3. Start the frontend development server:
   ```bash
   npm start
   ```

## Docker Deployment

### Using Docker Compose

1. Create a `.env` file in the project root:
   ```bash
   MONGODB_URI=your_mongodb_uri
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key
   ```

2. Build and start the containers:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

3. Access the application at `http://localhost:3000`

### Manual Docker Setup

1. Build the backend image:
   ```bash
   cd backend
   docker build -t product-review-analyzer-backend .
   ```

2. Build the frontend image:
   ```bash
   cd frontend
   docker build -t product-review-analyzer-frontend .
   ```

3. Run the containers:
   ```bash
   docker run -d -p 8000:8000 --env-file .env --name backend product-review-analyzer-backend
   docker run -d -p 3000:80 --name frontend product-review-analyzer-frontend
   ```

## Railway Deployment

Railway is a platform that makes it easy to deploy applications.

1. Connect your GitHub repository to Railway

2. Configure the following environment variables:
   - `MONGODB_URI`: Your MongoDB Atlas connection string
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SECRET_KEY`: A secure random string for JWT encryption
   - `PYTHON_VERSION`: 3.11

3. Deploy the application:
   - Select the repository
   - Configure the build settings
   - Deploy the application

4. Access your deployed application at the provided Railway URL

## Environment Variables

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGODB_URI` | MongoDB connection string | Yes | - |
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `SECRET_KEY` | Secret key for JWT encryption | Yes | - |
| `DEBUG` | Enable debug mode | No | `False` |
| `BATCH_SIZE_MULTIPLIER` | Adjust batch sizes | No | `1.0` |
| `CIRCUIT_BREAKER_TIMEOUT` | Circuit breaker timeout in seconds | No | `300` |
| `SLOW_PROCESSING_THRESHOLD` | Threshold for slow processing detection | No | `5` |
| `MAX_PARALLEL_WORKERS` | Maximum number of parallel workers | No | CPU count * 4 |

### Frontend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `REACT_APP_API_URL` | Backend API URL | Yes | - |

## Post-Deployment Verification

After deploying the application, verify that:

1. The backend API is accessible
2. The frontend can connect to the backend
3. Authentication is working properly
4. File uploads and analysis are functioning
5. WebSocket connections for progress updates are working

## Scaling Considerations

For high-traffic deployments, consider:

1. **Horizontal Scaling**:
   - Deploy multiple backend instances behind a load balancer
   - On AWS, use Elastic Load Balancer (ELB) with Auto Scaling Groups

2. **Database Scaling**:
   - Use MongoDB Atlas scaling options
   - Consider upgrading your MongoDB Atlas tier for higher performance

3. **Caching**:
   - Implement Redis for caching frequently accessed data
   - On AWS, consider using ElastiCache for Redis

4. **CDN**:
   - Use a CDN for static frontend assets
   - On AWS, use CloudFront for global content delivery

5. **Rate Limiting**:
   - Implement rate limiting for API endpoints
   - Consider using AWS API Gateway for managed API services

For AWS-specific scaling strategies, refer to the [AWS Deployment Guide](aws.md).
