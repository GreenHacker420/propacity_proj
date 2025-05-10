# MongoDB Integration

This document describes the MongoDB integration in the Product Review Analyzer application, including the fallback mechanisms for development and production environments.

## Overview

The Product Review Analyzer uses MongoDB Atlas as its primary database for storing user data, reviews, analysis history, and other application data. The application is designed to work in both development and production environments, with robust fallback mechanisms to ensure reliability.

## Key Features

- **Production-Ready**: Optimized for MongoDB Atlas in production environments
- **Development Mode**: Automatic fallback to mock MongoDB client in development mode
- **Graceful Degradation**: Continues to function even when MongoDB is unavailable
- **Enhanced Mock Client**: Sophisticated mock client that handles common operations
- **Collection Initialization**: Automatic creation of required collections

## Connection Management

### Connection Initialization

The application initializes the MongoDB connection during startup using the `init_mongodb()` function. This function:

1. Validates the MongoDB URI format
2. Attempts to connect to MongoDB Atlas
3. Tests the connection with a ping command
4. Initializes required collections if they don't exist
5. Falls back to a mock client in development mode if the connection fails

### Client Management

The `get_client()` function manages the MongoDB client instance:

- Returns an existing client if available
- Creates a new client with appropriate settings
- Falls back to a mock client in development mode if the connection fails
- Implements proper error handling and logging

### Collection Access

The `get_collection()` function provides access to MongoDB collections:

- Returns a collection from the specified database
- Verifies collection access with a test query
- Falls back to a mock collection in development mode if access fails
- Implements enhanced mocks for specific collections (e.g., processing_times)

## Development Mode

In development mode (`DEVELOPMENT_MODE=true`), the application provides a robust fallback mechanism:

- Automatically creates a mock MongoDB client if the real connection fails
- Simulates common MongoDB operations (find, insert, etc.)
- Returns realistic mock data for specific collections
- Logs detailed information about the fallback process

This allows developers to work on the application without requiring a MongoDB Atlas connection.

## Mock Client Implementation

The mock MongoDB client implementation:

- Simulates the MongoDB client interface
- Handles common operations like find, insert, update, and delete
- Returns appropriate mock data for different collections
- Implements proper error handling and logging

For example, the mock client for the `processing_times` collection returns realistic processing time estimates based on the operation and record count.

## Configuration

The MongoDB integration can be configured through environment variables:

- `MONGODB_URI`: MongoDB Atlas connection string (required)
- `DEVELOPMENT_MODE`: Set to "true" to enable mock client fallback (default: false)

Example `.env` file:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/product_reviews
DEVELOPMENT_MODE=true
```

## Collections

The application uses the following MongoDB collections:

- `users`: User accounts and authentication information
- `reviews`: Analyzed reviews and feedback
- `keywords`: Extracted keywords and their frequencies
- `analysis_history`: History of analysis operations with full summaries
- `processing_times`: Processing time records for estimation
- `weekly_summaries`: Weekly summaries for product prioritization

## Error Handling

The MongoDB integration includes comprehensive error handling:

- Connection errors: Falls back to mock client in development mode
- Authentication errors: Logs detailed error information
- Query errors: Returns appropriate error responses
- Network errors: Implements retry logic with backoff

## Logging

The system logs detailed information about the MongoDB connection process:

- `app.mongodb - INFO`: General information about the connection process
- `app.mongodb - WARNING`: Warnings about connection issues or fallbacks
- `app.mongodb - ERROR`: Errors that occurred during connection or queries

## Performance Considerations

- The application uses connection pooling for optimal performance
- Queries are optimized with appropriate indexes
- The mock client is designed to be lightweight and fast

## Troubleshooting

### Common Issues

1. **Connection failures**: Check if the MongoDB URI is correct and the Atlas cluster is accessible.

2. **Authentication errors**: Ensure the username and password in the MongoDB URI are correct.

3. **Network issues**: Check if the network allows connections to MongoDB Atlas (port 27017).

4. **Development mode not working**: Ensure `DEVELOPMENT_MODE=true` is set in the environment variables.

### Checking Connection Status

To check the MongoDB connection status, use the `/api/mongodb/status` endpoint:

```
GET /api/mongodb/status
```

This endpoint returns detailed information about the MongoDB connection, including:

- Connection status
- Server information
- Database statistics
- Collection information

## Related Documentation

- [Deployment Guide](./deployment/aws.md)
- [Environment Variables](../README.md#environment-variables)
- [API Documentation](./api/mongodb_api.md)
