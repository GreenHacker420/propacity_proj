# Product Review Analyzer Documentation

## Overview

The Product Review Analyzer is a comprehensive tool designed to help product managers and businesses analyze customer feedback efficiently. It processes reviews from various sources, performs sentiment analysis, extracts key insights, and generates actionable summaries to help prioritize product improvements.

### Key Capabilities

- Upload and analyze CSV files containing product reviews
- Scrape reviews from online sources (Twitter, Play Store)
- Perform sentiment analysis using both local models and Google's Gemini API
- Generate summaries of key pain points, feature requests, and positive feedback
- Visualize sentiment trends and common themes
- Store analysis history for future reference with full summaries
- Generate weekly summaries for product prioritization
- Real-time progress updates via WebSockets
- Parallel processing for improved performance
- Optimized batch processing with dynamic sizing
- Circuit breaker pattern for handling API rate limits

## Architecture

The Product Review Analyzer follows a client-server architecture:

- **Backend**: FastAPI-based Python application with WebSocket support
- **Frontend**: React with Tailwind CSS for the user interface
- **Database**: MongoDB Atlas for scalable data storage
- **AI Services**: Local models and Google Gemini API for advanced analysis
- **Real-time Communication**: WebSockets for progress updates
- **Parallel Processing**: Multi-threading for improved performance
- **Deployment Options**: AWS, Railway, and local deployment supported

### System Components Diagram

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│             │     │                     │     │                 │
│   Frontend  │◄───►│  FastAPI Backend    │◄───►│  MongoDB Atlas  │
│  (React)    │     │                     │     │                 │
│             │     └──────────┬──────────┘     └─────────────────┘
└─────────────┘                │
                               │
                     ┌─────────▼─────────┐
                     │                   │
                     │   AI Processing   │
                     │                   │
                     └───────┬───────────┘
                             │
               ┌─────────────┴─────────────┐
               │                           │
    ┌──────────▼──────────┐    ┌───────────▼────────────┐
    │                     │    │                        │
    │   Local Models      │    │   Google Gemini API    │
    │   (NLTK, spaCy)     │    │                        │
    │                     │    │                        │
    └─────────────────────┘    └────────────────────────┘
```

## Documentation Sections

- [Features](features/index.md): Detailed information about all features
  - [Batch Processing](features/batch-processing.md): Batch processing and progress reporting
  - [WebSocket Support](features/websocket.md): Real-time progress updates
  - [User Guide](features/user-guide.md): Instructions for using the application
- [API Reference](api/index.md): Complete API documentation
- [Deployment](deployment/index.md): Deployment instructions
  - [AWS Deployment](deployment/aws.md): Deploy on Amazon Web Services
  - [Railway Deployment](deployment/railway.md): Deploy on Railway
  - [Installation Guide](deployment/installation.md): Local installation instructions
- [Gemini API Integration](gemini_api_integration.md): Google Gemini API integration details
- [Troubleshooting](troubleshooting/index.md): Common issues and solutions

## Getting Started

To get started with the Product Review Analyzer:

1. See the [Installation Guide](deployment/installation.md) for setup instructions
2. Check the [User Guide](features/user-guide.md) for usage instructions
3. Explore the [API Documentation](api/index.md) if you're integrating with the system
4. For production deployment, see the [AWS Deployment Guide](deployment/aws.md) or [Railway Deployment Guide](deployment/railway.md)
5. Learn about [Batch Processing](features/batch-processing.md) and [WebSocket Support](features/websocket.md) for advanced features

## Contributing

If you'd like to contribute to the Product Review Analyzer, please check our [Contributing Guidelines](contributing.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.
