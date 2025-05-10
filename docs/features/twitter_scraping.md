# Twitter Data Generation and Scraping

This document describes the Twitter data generation and scraping functionality in the Product Review Analyzer application.

## Overview

The Twitter data generation feature allows users to obtain tweets related to a specific query for sentiment analysis and insight extraction. The system uses a three-tier approach to ensure reliable data availability:

1. **Primary Method**: Generate realistic Twitter data using Google's Gemini API
2. **Secondary Method**: Direct web scraping from Twitter/X or Nitter instances
3. **Fallback Method**: Local mock data generation

This approach ensures that the application always returns useful data, even when external services are unavailable or rate-limited.

## Implementation Details

### 1. Gemini API Data Generation

The primary method uses Google's Gemini API to generate realistic Twitter data based on the user's query. This approach has several advantages:

- **Reliability**: Not subject to Twitter API rate limits or scraping restrictions
- **Relevance**: Generated data is tailored to the specific query
- **Quality**: Produces high-quality, diverse content with realistic sentiment distribution
- **Consistency**: Always returns the requested number of tweets

The Gemini API is prompted to generate tweets that:
- Have diverse sentiment (positive, negative, neutral)
- Include a mix of opinions, questions, and statements
- Have realistic usernames and timestamps
- Include hashtags and mentions where appropriate
- Vary in length and style
- Are relevant to the query topic
- Include feature requests, complaints, and positive feedback

### 2. Direct Web Scraping

If the Gemini API is unavailable or fails, the system falls back to direct web scraping. This method attempts to scrape data from:

- Multiple Nitter instances (Twitter frontend alternatives)
- Direct Twitter/X scraping

The scraping process uses BeautifulSoup to extract tweet text, usernames, timestamps, and metrics from the HTML. This method is less reliable than the Gemini API approach due to:

- Frequent changes in Twitter's HTML structure
- Potential blocking of scraping attempts
- Nitter instances being occasionally unavailable

### 3. Local Mock Data Generation

As a final fallback, the system can generate mock Twitter data locally. This ensures that the application always returns some data, even when all external methods fail. The mock data:

- Is tailored to the query
- Has realistic usernames and timestamps
- Includes a variety of sentiment
- Has appropriate metrics (likes, retweets, etc.)

## Usage

To use the Twitter data generation feature, make a GET request to the `/api/scrape` endpoint with the following parameters:

- `source`: Set to "twitter"
- `query`: The search query (e.g., "product name")
- `limit`: Maximum number of tweets to return (default: 50, min: 1, max: 5000)

Example:
```
GET /api/scrape?source=twitter&query=iphone&limit=10
```

## Response Format

The endpoint returns a list of tweet objects with the following structure:

```json
[
  {
    "text": "The tweet text including any hashtags or mentions",
    "username": "username",
    "timestamp": "2023-05-10T12:34:56",
    "rating": null,
    "sentiment_score": 0.75,
    "sentiment_label": "POSITIVE",
    "category": "positive_feedback",
    "keywords": ["keyword1", "keyword2"],
    "source": "twitter",
    "metadata": {
      "author": "username",
      "date": "2023-05-10T12:34:56",
      "metrics": {
        "retweet_count": 5,
        "reply_count": 2,
        "like_count": 10,
        "quote_count": 1
      }
    }
  },
  // More tweets...
]
```

## Configuration

The Twitter data generation feature can be configured through environment variables:

- `GEMINI_API_KEY`: Google Gemini API key for enhanced data generation
- `GEMINI_MODEL`: Gemini model to use (default: gemini-2.0-flash)
- `DEVELOPMENT_MODE`: Set to "true" to enable mock data generation when other methods fail

## Troubleshooting

### Common Issues

1. **No data returned**: Check if the Gemini API key is valid and the API is available.

2. **Slow response times**: The direct web scraping method can be slow. Consider:
   - Reducing the `limit` parameter
   - Ensuring the Gemini API is properly configured

3. **Low-quality data**: If the data seems generic or unrelated to the query:
   - Check if the Gemini API is being used (look for "Generating Twitter data with Gemini API" in the logs)
   - Ensure the query is specific enough

### Logging

The system logs detailed information about the Twitter data generation process. Look for log messages with the following prefixes:

- `app.services.scraper - INFO`: General information about the scraping process
- `app.services.scraper - WARNING`: Warnings about failed scraping attempts
- `app.services.scraper - ERROR`: Errors that occurred during scraping

## Performance Considerations

- The Gemini API method is the fastest and most reliable
- Direct web scraping can be slow and may fail for large `limit` values
- Local mock data generation is very fast but produces less relevant data

For optimal performance, ensure the Gemini API is properly configured and available.

## Future Improvements

Planned improvements to the Twitter data generation feature include:

1. **Caching**: Implement caching of generated data to improve performance for repeated queries
2. **Enhanced Filtering**: Add options to filter tweets by date range, language, etc.
3. **Sentiment Pre-filtering**: Allow requesting only positive, negative, or neutral tweets
4. **Topic Clustering**: Group tweets by topic for better organization
5. **User Verification**: Indicate whether the tweet is from a verified user

## Related Documentation

- [Gemini API Integration](../gemini_api_integration.md)
- [MongoDB Integration](../mongodb_integration.md)
- [Sentiment Analysis](./sentiment_analysis.md)
