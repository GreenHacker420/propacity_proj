# Batch Processing and Progress Reporting

The Product Review Analyzer includes a sophisticated batch processing system designed to handle large volumes of reviews efficiently while providing real-time feedback to users.

## Overview

When processing large datasets (hundreds or thousands of reviews), the system:

1. Divides the data into optimally sized batches
2. Processes each batch efficiently
3. Reports progress in real-time via WebSockets
4. Provides accurate time estimates
5. Optimizes memory usage for large datasets

## Key Features

- **Dynamic Batch Sizing**: Automatically adjusts batch size based on review length
- **Real-time Progress Updates**: Shows processing status via WebSockets
- **Estimated Completion Time**: Dynamically calculates remaining processing time
- **Memory Optimization**: Implements techniques to handle very large datasets
- **Parallel Processing**: Uses multiple threads for efficient analysis

## Implementation Details

### Dynamic Batch Sizing Algorithm

The system automatically adjusts batch sizes based on the average length of reviews:

```python
# Calculate optimal batch size based on review length
avg_review_length = sum(len(review) for review in reviews) / len(reviews)

# Adjust batch size based on average review length - increased for better performance
if avg_review_length < 100:
    batch_size = 300  # Very short reviews
elif avg_review_length < 200:
    batch_size = 200  # Short reviews
elif avg_review_length < 500:
    batch_size = 150  # Medium reviews
else:
    batch_size = 100  # Long reviews
```

This algorithm ensures that:
- Shorter reviews are processed in larger batches for maximum efficiency
- Longer reviews are processed in smaller batches to avoid timeouts
- The system adapts to the specific content being analyzed
- Batch sizes are optimized for both performance and memory usage

### Progress Calculation

The system tracks several metrics during processing:

1. **Processing Speed**: Calculated as items processed divided by elapsed time
   ```python
   avg_speed = total_processed / sum(batch_times)
   ```

2. **Estimated Time Remaining**: Based on current processing speed
   ```python
   estimated_time_remaining = remaining_items / avg_speed
   ```

3. **Progress Percentage**: Simple percentage of completed items
   ```python
   progress_percentage = (items_processed / total_items) * 100
   ```

### Memory Optimization Techniques

The system implements several memory optimization techniques to handle very large datasets:

1. **Selective Caching**:
   ```python
   # Only cache if text is not too long to save memory
   if len(batch[j]) < 5000:  # Only cache texts shorter than 5000 chars
       self._add_to_cache(batch[j], result, "sentiment")
   ```

2. **Periodic Garbage Collection**:
   ```python
   # Force garbage collection to free memory
   if i % 5 == 0:  # Every 5 batches
       import gc
       gc.collect()
   ```

3. **Streaming Database Queries**:
   ```python
   # Use a batch size to limit memory usage
   cursor = reviews_collection.find(query).batch_size(500)

   # Process reviews in batches using the cursor
   async for review in cursor:
       # Process review
   ```

4. **Limited Trend Analysis**:
   ```python
   # Store a limited number of reviews for trend analysis
   if len(reviews_for_trends) < 1000:
       reviews_for_trends.append(review)
   ```

These optimizations allow the system to process datasets with tens of thousands of reviews without running out of memory.

### WebSocket Communication Flow

1. **Connection Establishment**:
   - Frontend connects to `/ws` endpoint with authentication token
   - Backend validates token and establishes connection
   - Connection is stored in active connections map

2. **Progress Updates**:
   - Backend sends JSON messages with progress information
   - Frontend updates UI based on received data
   - Messages include batch status, time estimates, and completion percentage

3. **Connection Management**:
   - Ping/pong messages maintain connection
   - Automatic reconnection on disconnection
   - Graceful handling of authentication failures

## Frontend Integration

The frontend displays batch processing progress using a dedicated component:

```jsx
<BatchProgress
  status={status}
  isVisible={isProcessing}
  onComplete={handleProcessingComplete}
/>
```

This component shows:
- Progress bar with completion percentage
- Current batch and total batches
- Items processed and total items
- Processing speed (items per second)
- Estimated time remaining

## Configuration Options

The batch processing system can be configured through environment variables:

- `BATCH_SIZE_MULTIPLIER`: Adjust all batch sizes (default: 1.0)
- `CIRCUIT_BREAKER_TIMEOUT`: Time before resetting circuit (default: 300 seconds)
- `SLOW_PROCESSING_THRESHOLD`: Threshold for slow processing detection (default: 5 seconds)
- `MAX_PARALLEL_WORKERS`: Maximum number of parallel workers (default: CPU count * 4)

## Best Practices

For optimal performance with batch processing:

1. **Preprocess Data**: Clean and normalize data before batch processing
2. **Monitor Memory Usage**: Watch for memory consumption with very large batches
3. **Use WebSocket UI**: Implement the progress UI for better user experience
4. **Handle Disconnections**: Implement reconnection logic in the frontend
5. **Test with Various Sizes**: Validate performance with different batch sizes

## Troubleshooting

Common issues and solutions:

### Slow Processing

**Symptoms**:
- Circuit breaker frequently opening
- Very slow processing times

**Solutions**:
- Reduce batch size using `BATCH_SIZE_MULTIPLIER`
- Increase parallel workers if CPU-bound
- Check network latency to API services

### Memory Issues

**Symptoms**:
- Application crashes during large batch processing
- Out of memory errors

**Solutions**:
- Reduce batch size
- Process data in smaller chunks
- Increase server memory if possible

### WebSocket Connection Issues

**Symptoms**:
- Progress bar not updating
- Frontend shows disconnected status

**Solutions**:
- Check authentication token
- Verify WebSocket server is running
- Implement automatic reconnection logic
