# Gemini API Integration Documentation

## Overview

The Product Review Analyzer integrates Google's Gemini API to provide advanced text analysis capabilities, including sentiment analysis, batch processing, and insight extraction. This document provides detailed information about the implementation, usage, and optimization techniques used in the integration.

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [API Endpoints](#api-endpoints)
5. [Optimization Techniques](#optimization-techniques)
6. [Error Handling](#error-handling)
7. [Performance Monitoring](#performance-monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Features

The Gemini API integration provides the following features:

- **Sentiment Analysis**: Analyze the sentiment of text with high accuracy
- **Batch Processing**: Process multiple reviews in batches for improved performance
- **Insight Extraction**: Extract key insights, pain points, feature requests, and positive aspects from reviews
- **Summary Generation**: Generate concise summaries from multiple reviews
- **Adaptive Throttling**: Automatically adjust request rates to avoid rate limits
- **Multi-Level Caching**: Cache results for faster response times
- **Circuit Breaker Pattern**: Gracefully degrade to local processing when API is unavailable
- **Performance Monitoring**: Track API performance metrics

## Architecture

The Gemini API integration is implemented in the `GeminiService` class, which provides a high-level interface for interacting with the Gemini API. The service is designed to be fault-tolerant, with automatic fallback to local processing when the API is unavailable or rate-limited.

### Component Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   API Routes    │────▶│  GeminiService  │────▶│   Gemini API    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │  ▲
                               │  │
                               ▼  │
┌─────────────────┐     ┌─────────────────┐
│  Local Fallback │◀───▶│  Cache System   │
└─────────────────┘     └─────────────────┘
```

### Key Components

- **GeminiService**: Main service for interacting with the Gemini API
- **Cache System**: Multi-level caching for sentiment, insights, and summaries
- **Circuit Breaker**: Detects API failures and switches to local processing
- **Request Throttling**: Prevents rate limit errors by controlling request rates
- **Local Fallback**: Provides basic functionality when the API is unavailable

## Configuration

### Environment Variables

The Gemini API integration can be configured using the following environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `GEMINI_MODEL`: The Gemini model to use (default: "gemini-2.0-flash")

### Example Configuration

```bash
# .env file
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

## API Endpoints

The following API endpoints are available for interacting with the Gemini API:

### Sentiment Analysis

```
POST /api/gemini/sentiment
```

Analyzes the sentiment of a single text.

**Request Body:**
```json
{
  "text": "This product is amazing!"
}
```

**Response:**
```json
{
  "score": 0.9,
  "label": "POSITIVE",
  "confidence": 0.85,
  "processing_time": 0.25
}
```

### Batch Processing

```
POST /api/gemini/batch
```

Analyzes the sentiment of multiple texts in a single request.

**Request Body:**
```json
{
  "texts": [
    "This product is amazing!",
    "I'm disappointed with the quality."
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "score": 0.9,
      "label": "POSITIVE",
      "confidence": 0.85
    },
    {
      "score": 0.2,
      "label": "NEGATIVE",
      "confidence": 0.75
    }
  ],
  "processing_time": 0.5
}
```

### Insight Extraction

```
POST /api/gemini/insights
```

Extracts insights from a collection of reviews.

**Request Body:**
```json
{
  "reviews": [
    "This product is amazing! The battery life is excellent.",
    "I'm disappointed with the quality. It broke after a week."
  ]
}
```

**Response:**
```json
{
  "summary": "Mixed feedback with praise for battery life but concerns about durability.",
  "key_points": ["Battery life is excellent", "Quality concerns"],
  "pain_points": ["Product broke after a week"],
  "feature_requests": ["No specific feature requests identified"],
  "positive_aspects": ["Battery life is excellent"],
  "processing_time": 0.75
}
```

### API Status

```
GET /api/gemini/status
```

Returns the current status of the Gemini API integration.

**Response:**
```json
{
  "available": true,
  "model": "gemini-2.0-flash",
  "rate_limited": false,
  "circuit_open": false,
  "using_local_processing": false,
  "performance": {
    "avg_response_time": 0.325,
    "total_api_calls": 150,
    "cache_hits": 75,
    "cache_misses": 25,
    "cache_hit_ratio": 0.75,
    "throttling": {
      "min_request_interval": 0.1,
      "requests_per_minute": 60
    }
  },
  "cache_stats": {
    "sentiment_cache_size": 500,
    "insight_cache_size": 100,
    "summary_cache_size": 50
  }
}
```

## Optimization Techniques

The Gemini API integration includes several advanced optimization techniques to improve performance and reliability:

### Intelligent Batch Processing

- Dynamically adjusts batch sizes based on review length
- Processes shorter reviews in larger batches for better efficiency
- Automatically falls back to local processing when rate limits are hit

```python
# Calculate optimal batch size based on review length
avg_review_length = sum(len(review) for review in reviews) / len(reviews)

# Adjust batch size based on average review length
if avg_review_length < 100:
    batch_size = 100  # Very short reviews
elif avg_review_length < 200:
    batch_size = 75   # Short reviews
elif avg_review_length < 500:
    batch_size = 50   # Medium reviews
else:
    batch_size = 30   # Long reviews
```

### Multi-Level Caching System

- Three separate caches for sentiment analysis, insights, and summaries
- LRU (Least Recently Used) cache implementation with timestamps
- Memory-efficient caching with hash-based keys for long texts
- Cache hit/miss tracking for performance monitoring

```python
# Create a cache key based on the text
# For long texts, use a hash to save memory
if len(text) > 1000:
    import hashlib
    # Use first 100 chars + hash of full text as key
    key = text[:100] + "_" + hashlib.md5(text.encode()).hexdigest()
else:
    key = text
```

### Adaptive Request Throttling

- Automatically adjusts request rates based on API response times
- Implements a sliding window rate limiter to prevent quota exhaustion
- Adds small delays between batch requests to avoid rate limits

```python
# Adjust the minimum interval based on recent performance
if self.total_api_calls > 10:
    # If we're getting a lot of errors, slow down more
    if self.consecutive_failures > 0:
        self.min_request_interval = min(1.0, self.min_request_interval * 1.5)
    # If things are going well, speed up slightly
    elif self.consecutive_failures == 0 and self.min_request_interval > 0.1:
        self.min_request_interval = max(0.1, self.min_request_interval * 0.9)
```

### Robust JSON Parsing

- Multiple fallback mechanisms for handling various JSON response formats
- Handles markdown code blocks, bracket detection, and quote normalization
- Detailed error logging for debugging JSON parsing issues

### Circuit Breaker Pattern

- Automatically detects API reliability issues
- Temporarily switches to local processing when API is unstable
- Self-healing with automatic recovery after cooling-off period
- Detailed status reporting for monitoring

```python
# Open the circuit breaker
def _open_circuit(self):
    self.circuit_open = True
    self.circuit_reset_time = time.time() + self.circuit_reset_timeout
    logger.warning(f"Circuit breaker OPENED. Bypassing Gemini API for {self.circuit_reset_timeout} seconds.")

# Check if the circuit breaker is open
def _check_circuit_breaker(self) -> bool:
    # If circuit is open, check if it's time to try closing it
    if self.circuit_open:
        current_time = time.time()
        if current_time >= self.circuit_reset_time:
            logger.info("Circuit breaker reset time reached. Attempting to close circuit.")
            self.circuit_open = False
            self.consecutive_failures = 0
            return False
        else:
            # Circuit still open
            time_remaining = int(self.circuit_reset_time - current_time)
            logger.info(f"Circuit breaker open. Using local processing for {time_remaining} more seconds.")
            return True
    # Circuit is closed
    return False
```

## Error Handling

The Gemini API integration includes comprehensive error handling to ensure robustness and reliability:

### JSON Parsing Errors

The service includes multiple fallback mechanisms for handling JSON parsing errors:

1. **Direct JSON Parsing**: Attempts to parse the response directly as JSON
2. **Markdown Code Block Extraction**: Extracts JSON from markdown code blocks
3. **Bracket Detection**: Finds JSON objects or arrays using bracket detection
4. **Quote Normalization**: Replaces single quotes with double quotes for valid JSON
5. **Fallback to Local Processing**: Uses local processing if all parsing attempts fail

```python
try:
    # Try to parse the response text as JSON directly
    result = json.loads(response.text)
except json.JSONDecodeError as e:
    logger.warning(f"JSON decode error: {str(e)}. Attempting to extract JSON from text.")
    # If parsing fails, try to extract JSON from the text with more robust handling
    text = response.text.strip()

    # Handle markdown code blocks
    if "```" in text:
        # Extract content between first ``` and last ```
        parts = text.split("```")
        for i, part in enumerate(parts):
            if i > 0 and i < len(parts) - 1:  # Skip first and last parts (outside ```)
                # Remove "json" if it's at the start of the code block
                if part.startswith("json"):
                    part = part[4:].strip()
                elif part.startswith("JSON"):
                    part = part[4:].strip()

                # Try to parse this part
                try:
                    result = json.loads(part.strip())
                    logger.info("Successfully extracted JSON from code block")
                    break
                except json.JSONDecodeError:
                    continue
```

### Rate Limit Handling

The service automatically detects rate limit errors and implements exponential backoff:

1. **Rate Limit Detection**: Detects 429 errors and quota-related errors
2. **Exponential Backoff**: Increases wait time exponentially after consecutive failures
3. **Automatic Recovery**: Automatically resets after the backoff period
4. **Fallback to Local Processing**: Uses local processing during rate limit periods

```python
# Check if this is a rate limit error
if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
    self.consecutive_failures += 1
    wait_time = min(300, self.initial_wait_time * (self.backoff_factor ** (self.consecutive_failures - 1)))

    # Set rate limiting flags
    self.rate_limited = True
    self.rate_limit_reset_time = time.time() + wait_time

    logger.warning(f"Rate limit exceeded. Using fallback for {wait_time} seconds.")

    # Check if we should open the circuit breaker
    if self.consecutive_failures >= self.failure_threshold:
        self._open_circuit()
```

### Local Fallback

The service includes a local fallback mechanism using VADER sentiment analysis:

```python
def _local_sentiment_analysis(self, text: str) -> Dict[str, Any]:
    """
    Perform local sentiment analysis when Gemini API is unavailable.
    """
    # Check cache first for faster processing
    cached_result = self._get_from_cache(text, "sentiment")
    if cached_result:
        return cached_result

    # Use VADER sentiment analyzer for speed
    if VADER_AVAILABLE:
        try:
            sentiment_scores = vader_analyzer.polarity_scores(text)
            compound_score = sentiment_scores['compound']

            # Convert compound score from [-1, 1] to [0, 1]
            normalized_score = (compound_score + 1) / 2

            # Determine sentiment label
            if compound_score >= 0.05:
                label = "POSITIVE"
            elif compound_score <= -0.05:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"

            # Calculate confidence based on the magnitude of the compound score
            confidence = abs(compound_score)

            result = {
                "score": normalized_score,
                "label": label,
                "confidence": confidence
            }

            # Cache the result
            self._add_to_cache(text, result, "sentiment")

            return result
        except Exception as e:
            logger.error(f"Error using VADER sentiment analyzer: {str(e)}")
            # Fall back to basic sentiment

    # Basic fallback if all else fails
    result = {"score": 0.5, "label": "NEUTRAL", "confidence": 0.0}
    self._add_to_cache(text, result, "sentiment")
    return result
```

## Performance Monitoring

The Gemini API integration includes comprehensive performance monitoring to track API usage, response times, and cache efficiency:

### Metrics Tracked

- **Average Response Time**: Average time for API calls
- **Total API Calls**: Total number of API calls made
- **Cache Hits/Misses**: Number of cache hits and misses
- **Cache Hit Ratio**: Percentage of requests served from cache
- **Request Throttling**: Current throttling settings
- **Cache Sizes**: Size of each cache (sentiment, insight, summary)

### Accessing Performance Metrics

Performance metrics can be accessed through the `/api/gemini/status` endpoint, which returns detailed information about the current state of the Gemini API integration.

```json
{
  "performance": {
    "avg_response_time": 0.325,
    "total_api_calls": 150,
    "cache_hits": 75,
    "cache_misses": 25,
    "cache_hit_ratio": 0.75,
    "throttling": {
      "min_request_interval": 0.1,
      "requests_per_minute": 60
    }
  },
  "cache_stats": {
    "sentiment_cache_size": 500,
    "insight_cache_size": 100,
    "summary_cache_size": 50
  }
}
```

## Troubleshooting

### Common Issues and Solutions

#### Rate Limit Errors

**Symptoms:**
- Frequent fallbacks to local processing
- Error messages containing "429" or "quota exceeded"
- High `consecutive_failures` count in status endpoint

**Solutions:**
- Reduce the number of requests by increasing batch sizes
- Implement client-side caching to reduce duplicate requests
- Consider upgrading your Gemini API quota
- Adjust the `max_requests_per_minute` setting to a lower value

#### JSON Parsing Errors

**Symptoms:**
- Error messages containing "JSONDecodeError"
- Frequent fallbacks to local processing
- Inconsistent results from the API

**Solutions:**
- Check the logs for the raw API responses to identify formatting issues
- Adjust the prompts to explicitly request proper JSON formatting
- Ensure the model is configured correctly (some models handle JSON better than others)
- Update to the latest version of the Gemini API client library

#### High Latency

**Symptoms:**
- Slow response times
- High `avg_response_time` in status endpoint
- Timeouts in client applications

**Solutions:**
- Increase batch sizes to process more reviews in a single request
- Optimize prompts to be more concise
- Implement more aggressive caching
- Consider using a faster Gemini model variant

#### Circuit Breaker Activation

**Symptoms:**
- `circuit_open: true` in status endpoint
- Consistent fallback to local processing
- Log messages about circuit breaker opening

**Solutions:**
- Check API key validity and quota
- Adjust the `failure_threshold` to be more tolerant
- Increase the `circuit_reset_timeout` to allow more time for recovery
- Monitor API status and retry when service is stable

### Logging and Debugging

The Gemini API integration includes comprehensive logging to help diagnose issues:

- **Info Level**: General operation information, performance metrics
- **Warning Level**: Rate limiting, circuit breaker activation, parsing issues
- **Error Level**: API errors, parsing failures, fallback activations

To enable more detailed logging, adjust the logging level in your configuration:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("gemini_service")
```

## Best Practices

### Optimizing Prompts

For best results with the Gemini API, follow these prompt optimization guidelines:

1. **Be Explicit About Format**: Clearly specify the expected JSON structure
2. **Include Examples**: Provide examples of the expected response format
3. **Keep Prompts Concise**: Remove unnecessary text to reduce token usage
4. **Use Consistent Formatting**: Use the same format for all requests
5. **Specify Field Types**: Indicate the expected data type for each field

Example of an optimized prompt:

```python
prompt = f"""
Analyze sentiment of these reviews. Return a valid JSON array with objects containing:
"score" (float 0-1, negative to positive), "label" (string: "POSITIVE"/"NEGATIVE"/"NEUTRAL"), "confidence" (float 0-1).

Example of expected format:
[
  {{"score": 0.8, "label": "POSITIVE", "confidence": 0.9}},
  {{"score": 0.2, "label": "NEGATIVE", "confidence": 0.7}}
]

Reviews:
{reviews_text}

IMPORTANT: Return ONLY the JSON array with no markdown formatting, no ```json tags, and no other text.
Use double quotes for all keys and string values.
"""
```

### Batch Size Optimization

Optimal batch sizes depend on the length and complexity of the reviews:

- **Very Short Reviews** (< 100 chars): 100 reviews per batch
- **Short Reviews** (100-200 chars): 75 reviews per batch
- **Medium Reviews** (200-500 chars): 50 reviews per batch
- **Long Reviews** (> 500 chars): 30 reviews per batch

### Caching Strategies

For optimal performance, implement these caching strategies:

1. **Cache Frequently Analyzed Texts**: Prioritize caching for common reviews
2. **Use LRU Eviction**: Remove least recently used items when cache is full
3. **Implement TTL**: Set a time-to-live for cache entries to ensure freshness
4. **Use Memory-Efficient Keys**: Hash long texts to save memory
5. **Monitor Cache Hit Ratio**: Aim for at least 70% cache hit ratio

### Rate Limit Management

To avoid rate limit issues:

1. **Implement Exponential Backoff**: Increase wait time after consecutive failures
2. **Monitor API Usage**: Track API calls to stay within quota
3. **Distribute Requests**: Spread requests evenly over time
4. **Prioritize Important Requests**: Use local processing for less critical analyses
5. **Implement Request Queuing**: Queue requests during rate limit periods

## Conclusion

The Gemini API integration in the Product Review Analyzer provides powerful text analysis capabilities with advanced optimization techniques for performance, reliability, and fault tolerance. By following the guidelines in this documentation, you can effectively use and troubleshoot the Gemini API integration in your application.