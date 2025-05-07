# API Reference

The Product Review Analyzer exposes a comprehensive REST API for integration with other systems. This documentation provides details about all available endpoints, request/response formats, and authentication requirements.

## Base URL

All API endpoints are relative to the base URL:

```
https://your-deployment-url.com/api
```

## Authentication

Most API endpoints require authentication using JWT (JSON Web Token). Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

To obtain a token, use the [authentication endpoint](#authentication-endpoints).

## API Endpoints

- [Authentication Endpoints](#authentication-endpoints)
- [Analysis Endpoints](#analysis-endpoints)
- [History Endpoints](#history-endpoints)
- [Weekly Summary Endpoints](#weekly-summary-endpoints)
- [WebSocket Endpoints](#websocket-endpoints)

### Authentication Endpoints

#### `POST /auth/token`

Authenticate user and get access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

### Analysis Endpoints

#### `POST /analyze`

Analyze reviews and return results.

**Request Body:**
```json
[
  {
    "text": "string",
    "metadata": {
      "source": "string",
      "category": "string",
      "id": "string"
    }
  }
]
```

**Response:**
```json
[
  {
    "id": "string",
    "text": "string",
    "sentiment": "string",
    "score": 0.0,
    "keywords": ["string"],
    "summary": "string",
    "insights": {
      "pain_points": ["string"],
      "feature_requests": ["string"],
      "positive_feedback": ["string"]
    },
    "metadata": {
      "source": "string",
      "category": "string",
      "id": "string"
    }
  }
]
```

#### `POST /upload`

Upload CSV file with reviews for analysis.

**Request:**
- Form data with file upload

**Response:**
Same as `/analyze`

#### `GET /scrape`

Scrape and analyze reviews from external sources.

**Query Parameters:**
- `source`: Data source (twitter, playstore)
- `query`: Search query or app URL
- `limit`: Maximum number of reviews to fetch (default: 50)

**Response:**
Same as `/analyze`

### History Endpoints

#### `GET /history`

Get analysis history.

**Query Parameters:**
- `limit`: Maximum number of results (default: 10)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "total": 0,
  "items": [
    {
      "id": "string",
      "timestamp": "string",
      "source": "string",
      "review_count": 0,
      "summary": "string"
    }
  ]
}
```

#### `GET /history/{id}`

Get details of a specific analysis.

**Response:**
```json
{
  "id": "string",
  "timestamp": "string",
  "source": "string",
  "review_count": 0,
  "summary": "string",
  "reviews": [
    // Same as /analyze response
  ]
}
```

### Weekly Summary Endpoints

#### `GET /weekly`

Get weekly summary of reviews.

**Query Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "period": {
    "start": "string",
    "end": "string"
  },
  "total_reviews": 0,
  "sentiment_distribution": {
    "positive": 0.0,
    "neutral": 0.0,
    "negative": 0.0
  },
  "top_topics": [
    {
      "topic": "string",
      "count": 0,
      "sentiment": 0.0
    }
  ],
  "key_insights": {
    "pain_points": ["string"],
    "feature_requests": ["string"],
    "positive_feedback": ["string"]
  },
  "recommendations": ["string"]
}
```

### WebSocket Endpoints

#### `WebSocket /ws`

Connect to receive real-time updates during batch processing.

**Query Parameters:**
- `token`: JWT authentication token

**Messages Received:**
```json
{
  "type": "batch_progress",
  "current_batch": 0,
  "total_batches": 0,
  "batch_time": 0.0,
  "items_processed": 0,
  "total_items": 0,
  "avg_speed": 0.0,
  "estimated_time_remaining": 0.0,
  "progress_percentage": 0.0
}
```

## Error Handling

All API endpoints use standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message"
}
```

## Rate Limiting

API endpoints may be subject to rate limiting. When rate limited, the API will return a `429 Too Many Requests` status code with headers indicating the rate limit status:

- `X-RateLimit-Limit`: Maximum requests per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

## Pagination

Endpoints that return multiple items support pagination using `limit` and `offset` parameters:

- `limit`: Maximum number of items to return (default varies by endpoint)
- `offset`: Number of items to skip (default: 0)

Paginated responses include metadata:

```json
{
  "total": 100,  // Total number of items
  "items": [     // Array of items for current page
    // ...
  ]
}
```
