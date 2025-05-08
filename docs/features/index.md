# Features

The Product Review Analyzer offers a comprehensive set of features designed to help product managers and development teams make data-driven decisions based on user feedback.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![React](https://img.shields.io/badge/React-Latest-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)
![AI](https://img.shields.io/badge/AI-Gemini_API-red)
![NLP](https://img.shields.io/badge/NLP-Sentiment_Analysis-yellow)
![Deployment](https://img.shields.io/badge/Deployment-AWS_EC2-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Core Features

- [Data Input Methods](data-input.md): Upload CSV files, scrape from online sources, or enter reviews manually
- [Sentiment Analysis](sentiment-analysis.md): Determine if reviews are positive, negative, or neutral
- [Insight Extraction](insight-extraction.md): Extract actionable insights from reviews
- [Batch Processing](batch-processing.md): Process large volumes of reviews efficiently
- [Visualization](visualization.md): Visual representation of analysis results
- [Weekly Summaries](weekly-summaries.md): Aggregated insights for product prioritization
- [History Tracking](history-tracking.md): Access past analyses and track changes over time

## Feature Highlights

### Data Input Methods

The system supports multiple ways to input review data:

- **CSV Upload**: Upload files with review data
- **Web Scraping**: Fetch reviews from Twitter or Google Play Store
- **Direct Input**: Enter reviews manually for analysis

### Analysis Capabilities

The system performs several types of analysis:

- **Sentiment Analysis**: Determine if reviews are positive, negative, or neutral
- **Key Topic Extraction**: Identify common themes and topics
- **Insight Generation**: Extract actionable insights from reviews
- **Summary Creation**: Generate concise summaries of review content

### Batch Processing with Progress Reporting

Process large volumes of reviews efficiently:

- **Dynamic Batch Sizing**: Automatically adjusts batch size based on review length
- **Real-time Progress Updates**: Shows processing status via WebSockets
- **Estimated Completion Time**: Dynamically calculates remaining processing time
- **Circuit Breaker Pattern**: Falls back to local processing when API is slow or unavailable

### Visualization and Reporting

Visualize analysis results for better understanding:

- **Sentiment Distribution**: Visual breakdown of positive/negative/neutral reviews
- **Topic Clustering**: Grouping of reviews by common themes
- **Weekly Summaries**: Aggregated insights for product prioritization
- **Historical Analysis**: Track sentiment changes over time

## Feature Documentation

For detailed information about each feature, please refer to the specific feature documentation:

- [Data Input Methods](data-input.md)
- [Sentiment Analysis](sentiment-analysis.md)
- [Insight Extraction](insight-extraction.md)
- [Batch Processing](batch-processing.md)
- [Visualization](visualization.md)
- [Weekly Summaries](weekly-summaries.md): Aggregated insights for product prioritization
- [WebSocket Support](websocket.md): Real-time progress updates
- [History Tracking](history-tracking.md)
