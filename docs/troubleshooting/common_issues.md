# Troubleshooting Common Issues

This guide addresses common issues you might encounter when running the Product Review Analyzer application and provides solutions to resolve them.

## Table of Contents

1. [MongoDB Connection Issues](#mongodb-connection-issues)
2. [Twitter Scraping Issues](#twitter-scraping-issues)
3. [API Endpoint Errors](#api-endpoint-errors)
4. [WebSocket Connection Issues](#websocket-connection-issues)
5. [Gemini API Issues](#gemini-api-issues)
6. [Performance Issues](#performance-issues)
7. [Deployment Issues](#deployment-issues)

## MongoDB Connection Issues

### Issue: MongoDB Connection Failures

**Symptoms:**
- Error messages like "Failed to connect to MongoDB"
- Application fails to start in production mode
- Database operations fail with connection errors

**Solutions:**
1. **Check MongoDB URI**: Ensure the MongoDB URI in your `.env` file is correct.
2. **Network Access**: Verify that your IP address is allowed in the MongoDB Atlas network access settings.
3. **Credentials**: Confirm that the username and password in the URI are correct.
4. **Development Mode**: Set `DEVELOPMENT_MODE=true` to use the mock MongoDB client during development.

### Issue: MongoDB Authentication Errors

**Symptoms:**
- Error messages like "Authentication failed"
- Application starts but database operations fail

**Solutions:**
1. **Check Credentials**: Verify the username and password in the MongoDB URI.
2. **Database User**: Ensure the database user has the correct permissions.
3. **Auth Source**: Check if you need to specify an auth source in the URI (`?authSource=admin`).

## Twitter Scraping Issues

### Issue: No Twitter Data Returned

**Symptoms:**
- Empty array returned from `/api/scrape?source=twitter`
- Error messages in the logs about Twitter scraping failures

**Solutions:**
1. **Gemini API Key**: Ensure your Gemini API key is valid and properly configured.
2. **Query Specificity**: Use more specific queries to get better results.
3. **Limit Parameter**: Try reducing the `limit` parameter to a smaller value.
4. **Development Mode**: Set `DEVELOPMENT_MODE=true` to ensure fallback to mock data.

### Issue: Twitter Scraping is Slow

**Symptoms:**
- Long response times for Twitter scraping requests
- Timeouts when scraping Twitter data

**Solutions:**
1. **Gemini API**: Ensure the Gemini API is properly configured for faster responses.
2. **Reduce Limit**: Lower the `limit` parameter to request fewer tweets.
3. **Check Logs**: Look for warnings about fallbacks to slower scraping methods.

## API Endpoint Errors

### Issue: 504 Gateway Timeout Errors

**Symptoms:**
- 504 Gateway Timeout responses from API endpoints
- Frontend cancels operations and returns to the menu

**Solutions:**
1. **Increase Timeout**: Configure your reverse proxy (e.g., Nginx) with longer timeouts.
2. **Optimize Endpoints**: Check if the endpoint is performing heavy processing that can be optimized.
3. **Batch Processing**: Use smaller batch sizes for large operations.

### Issue: 413 Request Entity Too Large

**Symptoms:**
- 413 errors when sending large payloads to endpoints like `/api/api/summary`

**Solutions:**
1. **Nginx Configuration**: Increase the `client_max_body_size` in your Nginx configuration.
2. **Batch Processing**: Split large requests into smaller batches.
3. **Compression**: Use compression for large payloads.

## WebSocket Connection Issues

### Issue: WebSocket Connection Failures

**Symptoms:**
- WebSocket connections rejected with 403 Forbidden
- Mixed Content errors in the browser console

**Solutions:**
1. **Secure WebSockets**: Use `wss://` instead of `ws://` in production environments.
2. **Relative URLs**: Use relative WebSocket URLs (`/ws`) instead of absolute URLs.
3. **Nginx Configuration**: Ensure Nginx is properly configured for WebSocket proxying.

### Issue: WebSocket Disconnections

**Symptoms:**
- Frequent WebSocket disconnections
- Progress updates stop during processing

**Solutions:**
1. **Ping/Pong**: Implement WebSocket ping/pong to keep connections alive.
2. **Reconnection Logic**: Add automatic reconnection logic in the frontend.
3. **Timeout Configuration**: Increase timeout settings in your proxy configuration.

## Gemini API Issues

### Issue: Gemini API Rate Limits

**Symptoms:**
- Error messages about Gemini API rate limits
- Circuit breaker opening frequently

**Solutions:**
1. **Circuit Breaker**: The application automatically handles rate limits with the circuit breaker pattern.
2. **Batch Size**: Reduce the `GEMINI_BATCH_SIZE` environment variable.
3. **Local Processing**: Set `DEVELOPMENT_MODE=true` to use local processing when the circuit breaker is open.

### Issue: Gemini API Slow Responses

**Symptoms:**
- Long processing times for Gemini API requests
- Timeouts during batch processing

**Solutions:**
1. **Slow Threshold**: Adjust the `GEMINI_SLOW_THRESHOLD` environment variable.
2. **Model Selection**: Try using a faster Gemini model by setting `GEMINI_MODEL`.
3. **Parallel Processing**: Ensure parallel processing is enabled for better performance.

## Performance Issues

### Issue: Slow Sentiment Analysis

**Symptoms:**
- Long processing times for sentiment analysis
- High CPU usage during analysis

**Solutions:**
1. **Batch Size**: Optimize batch sizes for your hardware.
2. **Parallel Processing**: Ensure `PARALLEL_PROCESSING=true` is set.
3. **Worker Count**: Adjust `MAX_WORKERS` based on your CPU cores.
4. **Model Optimization**: Use optimized models for sentiment analysis.

### Issue: High Memory Usage

**Symptoms:**
- Application crashes with out-of-memory errors
- Slow performance due to memory pressure

**Solutions:**
1. **Batch Processing**: Process data in smaller batches.
2. **Memory Optimization**: Implement memory-efficient data structures.
3. **Resource Limits**: Set appropriate resource limits for your deployment.

## Deployment Issues

### Issue: Deployment Failures

**Symptoms:**
- Application fails to start after deployment
- Error messages in deployment logs

**Solutions:**
1. **Environment Variables**: Ensure all required environment variables are set.
2. **Dependencies**: Verify that all dependencies are installed correctly.
3. **Permissions**: Check file and directory permissions.
4. **Logs**: Review application logs for specific error messages.

### Issue: Nginx Configuration Problems

**Symptoms:**
- 502 Bad Gateway errors
- Unable to access the application through Nginx

**Solutions:**
1. **Proxy Configuration**: Verify the Nginx proxy configuration.
2. **Port Binding**: Ensure the application is running and bound to the correct port.
3. **WebSocket Configuration**: Check WebSocket proxy settings in Nginx.
4. **SSL Configuration**: Verify SSL certificate configuration.

## Getting Help

If you're still experiencing issues after trying these solutions, please:

1. **Check Logs**: Review the application logs for detailed error messages.
2. **Search Issues**: Check if your issue has been reported in the GitHub repository.
3. **Create an Issue**: If your issue is new, create a detailed issue in the GitHub repository.
4. **Contact Support**: Reach out to the development team for assistance.

## Related Documentation

- [MongoDB Integration](../mongodb_integration.md)
- [Twitter Scraping](../features/twitter_scraping.md)
- [Gemini API Integration](../gemini_api_integration.md)
- [Deployment Guide](../deployment/aws.md)
