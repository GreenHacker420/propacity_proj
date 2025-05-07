# Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the Product Review Analyzer.

## Common Issues

- [API Connection Issues](#api-connection-issues)
- [Authentication Problems](#authentication-problems)
- [File Upload Issues](#file-upload-issues)
- [Gemini API Issues](#gemini-api-issues)
- [Performance Problems](#performance-problems)
- [WebSocket Connection Issues](#websocket-connection-issues)
- [Database Issues](#database-issues)

## API Connection Issues

### Symptoms
- Frontend cannot connect to backend API
- API requests timeout or fail
- Error messages about connection refused

### Solutions
1. **Check API URL Configuration**:
   - Verify the `REACT_APP_API_URL` in frontend `.env` file
   - Ensure the URL includes the correct protocol (http/https)
   - Check that the port number is correct (default: 8000)

2. **Check CORS Configuration**:
   - Verify that CORS is properly configured in the backend
   - Check that the frontend origin is allowed in CORS settings

3. **Check Network Connectivity**:
   - Ensure there are no network issues between frontend and backend
   - Check firewall settings that might block connections

4. **Verify API Server Status**:
   - Confirm the backend server is running
   - Check backend logs for error messages
   - Try accessing the API documentation at `/docs` endpoint

## Authentication Problems

### Symptoms
- Unable to log in
- "Unauthorized" errors when accessing protected endpoints
- Token validation failures

### Solutions
1. **Check Credentials**:
   - Verify username and password are correct
   - Ensure the user account exists and is active

2. **Check JWT Configuration**:
   - Verify the `SECRET_KEY` environment variable is set
   - Check that the token expiration time is appropriate
   - Ensure the frontend is storing and sending the token correctly

3. **Token Issues**:
   - Clear browser storage and try logging in again
   - Check if the token is expired
   - Verify the token format is correct

4. **User Permissions**:
   - Ensure the user has the necessary permissions
   - Check role-based access control settings

## File Upload Issues

### Symptoms
- File uploads fail
- Timeout during upload
- Error messages about file size or format

### Solutions
1. **Check File Size**:
   - Verify the file is within the size limit (default: 10MB)
   - Try splitting large files into smaller chunks

2. **Check File Format**:
   - Ensure the file is in CSV format
   - Check for encoding issues (use UTF-8 encoding)
   - Verify the CSV structure matches expected format

3. **Server Configuration**:
   - Check server upload limits in FastAPI settings
   - Verify temporary file storage has sufficient space
   - Increase timeout settings for large file uploads

4. **Network Issues**:
   - Check for network stability during upload
   - Try a wired connection instead of Wi-Fi for large files

## Gemini API Issues

### Symptoms
- Circuit breaker frequently opening
- Slow processing times
- Error messages about rate limits or API failures

### Solutions
1. **API Key Issues**:
   - Verify the `GEMINI_API_KEY` is valid and active
   - Check if the API key has sufficient quota
   - Ensure the API key has the necessary permissions

2. **Rate Limiting**:
   - Reduce batch size using `BATCH_SIZE_MULTIPLIER` environment variable
   - Implement exponential backoff for retries
   - Upgrade to a higher API quota tier if needed

3. **Circuit Breaker Tuning**:
   - Adjust `CIRCUIT_BREAKER_TIMEOUT` for your use case
   - Modify `SLOW_PROCESSING_THRESHOLD` based on network conditions
   - Check logs for specific API error messages

4. **Fallback Configuration**:
   - Ensure local processing is properly configured
   - Verify that fallback mechanisms are working correctly
   - Consider using more local processing for non-critical analyses

## Performance Problems

### Symptoms
- Slow processing of large datasets
- High memory usage
- Application crashes during processing

### Solutions
1. **Batch Size Optimization**:
   - Adjust batch sizes based on review length
   - Reduce `BATCH_SIZE_MULTIPLIER` for memory-constrained environments
   - Monitor memory usage during processing

2. **Parallel Processing**:
   - Adjust `MAX_PARALLEL_WORKERS` based on available CPU cores
   - Avoid setting too high to prevent CPU contention
   - Consider CPU vs. I/O bound operations

3. **Database Optimization**:
   - Create appropriate indexes in MongoDB
   - Implement caching for frequently accessed data
   - Optimize database queries

4. **Resource Allocation**:
   - Increase server resources (CPU, memory)
   - Use dedicated servers for high-volume processing
   - Consider distributed processing for very large datasets

## WebSocket Connection Issues

### Symptoms
- Progress bar not updating
- Frontend shows disconnected status
- Real-time updates not working

### Solutions
1. **Connection Setup**:
   - Verify WebSocket URL is correct
   - Check that authentication token is being passed
   - Ensure WebSocket server is running

2. **Authentication Issues**:
   - Verify token is valid for WebSocket connections
   - Check token expiration and refresh mechanism
   - Ensure proper error handling for authentication failures

3. **Network Problems**:
   - Check for firewalls blocking WebSocket connections
   - Verify proxy settings if using a proxy
   - Test on different networks to isolate issues

4. **Reconnection Logic**:
   - Implement automatic reconnection in the frontend
   - Add exponential backoff for reconnection attempts
   - Handle connection state properly in the UI

## Database Issues

### Symptoms
- Database connection errors
- Slow queries
- Data not being saved or retrieved correctly

### Solutions
1. **Connection Issues**:
   - Verify `MONGODB_URI` is correct
   - Check network connectivity to MongoDB Atlas
   - Ensure IP whitelist includes your server IP

2. **Authentication Problems**:
   - Verify database username and password
   - Check database user permissions
   - Ensure the database exists and is accessible

3. **Performance Issues**:
   - Create appropriate indexes for common queries
   - Monitor query performance in MongoDB Atlas
   - Optimize data structure for your access patterns

4. **Data Integrity**:
   - Implement validation for data being saved
   - Add error handling for database operations
   - Use transactions for critical operations

## Getting Additional Help

If you're still experiencing issues after trying the solutions above:

1. **Check Logs**:
   - Review backend logs for detailed error messages
   - Check browser console for frontend errors
   - Look for specific error codes or messages

2. **Community Support**:
   - Post your issue on the project's GitHub Issues page
   - Provide detailed information about your environment
   - Include steps to reproduce the issue

3. **Contact Maintainers**:
   - Reach out to the project maintainers directly
   - Provide logs and environment details
   - Explain what you've already tried
