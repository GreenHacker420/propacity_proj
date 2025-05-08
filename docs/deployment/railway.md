# Railway Deployment Guide

This guide provides step-by-step instructions for deploying the Product Review Analyzer on [Railway](https://railway.app/), a modern cloud platform that makes deployment simple and efficient.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up Railway](#setting-up-railway)
3. [Connecting Your Repository](#connecting-your-repository)
4. [Environment Configuration](#environment-configuration)
5. [Deployment](#deployment)
6. [Monitoring and Logs](#monitoring-and-logs)
7. [Custom Domain Setup](#custom-domain-setup)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying to Railway, ensure you have:

1. A [Railway account](https://railway.app/) (free tier available)
2. Your project code in a GitHub repository
3. MongoDB Atlas account with a configured cluster
4. Google Gemini API key (optional but recommended)

## Setting Up Railway

1. Sign up or log in to [Railway](https://railway.app/)
2. From the Railway dashboard, click "New Project"
3. Select "Deploy from GitHub repo"

## Connecting Your Repository

1. If you haven't connected your GitHub account yet, Railway will prompt you to do so
2. Once connected, select your Product Review Analyzer repository
3. Railway will automatically detect that your project has both frontend and backend components

## Environment Configuration

Configure the following environment variables in the Railway dashboard:

### Required Variables

- `MONGODB_URI`: Your MongoDB Atlas connection string
- `SECRET_KEY`: A secure random string for JWT token generation
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time (e.g., 1440 for 24 hours)
- `PORT`: Set to 8000 for the backend service
- `HOST`: Set to 0.0.0.0 to bind to all interfaces

### Optional Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_MODEL`: The Gemini model to use (default: gemini-2.0-flash)
- `GEMINI_BATCH_SIZE`: Number of reviews to process in each batch (default: 10)
- `GEMINI_SLOW_THRESHOLD`: Threshold in seconds to detect slow processing (default: 5)
- `DEBUG`: Set to False for production deployment
- `ENABLE_WEBSOCKETS`: Set to True to enable WebSocket support
- `PARALLEL_PROCESSING`: Set to True to enable parallel processing
- `MAX_WORKERS`: Number of worker threads for parallel processing (default: 4)

## Deployment

Railway will automatically deploy your application when you push changes to your repository. To manually deploy:

1. Go to your project in the Railway dashboard
2. Click on the "Deploy" tab
3. Click "Deploy Now"

Railway will build and deploy both the frontend and backend components of your application.

### Build Configuration

Railway automatically detects the build configuration for your project. For the Product Review Analyzer:

- **Backend**: Railway will use the `requirements.txt` file to install dependencies
- **Frontend**: Railway will use the `package.json` file to build the frontend

### Service Configuration

For optimal performance, configure the following in the Railway dashboard:

1. **Memory**: Allocate at least 512MB for the backend service
2. **CPU**: Allocate at least 0.5 CPU for the backend service
3. **Scaling**: Start with 1 instance and scale as needed

## Monitoring and Logs

Railway provides comprehensive monitoring and logging:

1. Go to your project in the Railway dashboard
2. Click on the "Metrics" tab to view performance metrics
3. Click on the "Logs" tab to view application logs

### Key Metrics to Monitor

- **Memory Usage**: Watch for spikes during large batch processing
- **CPU Usage**: Monitor during parallel processing operations
- **Response Time**: Track API endpoint performance
- **Error Rate**: Monitor for increased error rates

## Custom Domain Setup

To use a custom domain with your Railway deployment:

1. Go to your project in the Railway dashboard
2. Click on the "Settings" tab
3. Under "Domains", click "Generate Domain" or "Custom Domain"
4. Follow the instructions to configure your domain

## Troubleshooting

### Common Issues

#### Application Crashes During Startup

**Symptoms**:
- Deployment fails
- Logs show startup errors

**Solutions**:
- Check that all required environment variables are set
- Verify MongoDB connection string is correct
- Ensure Python version is compatible (use Python 3.11)

#### Memory Issues During Large Batch Processing

**Symptoms**:
- Application crashes during processing
- Logs show memory-related errors

**Solutions**:
- Increase memory allocation in Railway dashboard
- Reduce batch size using `GEMINI_BATCH_SIZE` environment variable
- Set `BATCH_SIZE_MULTIPLIER` to a value less than 1.0

#### WebSocket Connection Issues

**Symptoms**:
- Frontend shows disconnected status
- Real-time updates not working

**Solutions**:
- Ensure `ENABLE_WEBSOCKETS` is set to True
- Check Railway's WebSocket support configuration
- Verify frontend WebSocket URL is correct

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [Railway documentation](https://docs.railway.app/)
2. Review the application logs in the Railway dashboard
3. Check the [Product Review Analyzer troubleshooting guide](../troubleshooting/index.md)

## Performance Optimization

For optimal performance on Railway:

1. **Optimize Memory Usage**:
   - Set appropriate batch sizes
   - Enable garbage collection during processing
   - Use streaming for large datasets

2. **Reduce Cold Starts**:
   - Configure Railway to prevent service hibernation
   - Use a paid tier for production deployments

3. **Optimize Database Connections**:
   - Use connection pooling
   - Implement proper connection closing
   - Choose a MongoDB Atlas region close to your Railway deployment

## Security Considerations

When deploying to Railway:

1. **Secure Environment Variables**:
   - Never commit sensitive variables to your repository
   - Use Railway's environment variable management

2. **API Rate Limiting**:
   - Implement rate limiting for public endpoints
   - Configure the circuit breaker pattern for external API calls

3. **Authentication**:
   - Ensure JWT secrets are strong and unique
   - Set appropriate token expiration times
