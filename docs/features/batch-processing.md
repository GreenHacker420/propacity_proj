# Batch Processing and Progress Reporting

The Product Review Analyzer includes a sophisticated batch processing system designed to handle large volumes of reviews efficiently while providing real-time feedback to users.

## Overview

When processing large datasets (hundreds or thousands of reviews), the system:

1. Divides the data into optimally sized batches
2. Processes each batch efficiently using parallel processing
3. Reports progress in real-time via WebSockets
4. Provides accurate time estimates with dynamic updates
5. Optimizes memory usage for large datasets
6. Gracefully handles API rate limits with circuit breaker pattern

## Key Features

- **Dynamic Batch Sizing**: Automatically adjusts batch size based on review length
- **Real-time Progress Updates**: Shows processing status via WebSockets
- **Estimated Completion Time**: Dynamically calculates remaining processing time
- **Memory Optimization**: Implements techniques to handle very large datasets (73,000+ reviews)
- **Parallel Processing**: Uses multiple threads for efficient analysis
- **Circuit Breaker Pattern**: Falls back to local processing when API limits are hit
- **RAM Usage Optimization**: Dynamically adjusts batch sizes based on available memory
- **WebSocket Integration**: Provides real-time updates to the frontend

## Implementation Details

### Dynamic Batch Sizing Algorithm

The system automatically adjusts batch sizes based on the average length of reviews and available system resources:

```python
# Calculate optimal batch size based on review length
avg_review_length = sum(len(review) for review in reviews) / len(reviews)

# Get available system memory
import psutil
available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)

# Base batch size calculation
if avg_review_length < 100:
    batch_size = 500  # Very short reviews
elif avg_review_length < 200:
    batch_size = 300  # Short reviews
elif avg_review_length < 500:
    batch_size = 200  # Medium reviews
else:
    batch_size = 150  # Long reviews

# Adjust based on available memory
memory_factor = min(1.0, available_memory_mb / 1000)  # Scale down if less than 1GB available
batch_size = int(batch_size * memory_factor)

# Apply environment variable multiplier if set
batch_size_multiplier = float(os.getenv("BATCH_SIZE_MULTIPLIER", 1.0))
batch_size = int(batch_size * batch_size_multiplier)

# Ensure minimum batch size
batch_size = max(batch_size, 50)
```

This algorithm ensures that:
- Shorter reviews are processed in larger batches for maximum efficiency
- Longer reviews are processed in smaller batches to avoid timeouts
- The system adapts to the specific content being analyzed
- Batch sizes are optimized for both performance and memory usage
- Available system memory is considered to prevent out-of-memory errors
- Administrators can fine-tune batch sizes using environment variables

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
   - Frontend connects to `/ws/batch-progress` or `/ws/sentiment-progress` endpoint with authentication token
   - Backend validates token and establishes connection
   - Connection is stored in active connections map with client ID

2. **Progress Updates**:
   - Backend sends JSON messages with progress information
   - Frontend updates UI based on received data in real-time
   - Messages include batch status, time estimates, completion percentage, and processing speed
   - Updates are sent after each batch completes

3. **Connection Management**:
   - Ping/pong messages maintain connection
   - Automatic reconnection on disconnection with exponential backoff
   - Graceful handling of authentication failures
   - Support for multiple simultaneous clients

4. **Circuit Breaker Status**:
   - WebSocket sends notifications when circuit breaker opens or closes
   - Frontend displays appropriate messages about API status
   - Users are informed when processing switches to local mode

For detailed WebSocket implementation, see the [WebSocket Documentation](websocket.md).

## Frontend Integration

The frontend displays batch processing progress using a dedicated component that connects to the WebSocket API:

```jsx
import { useWebSocket } from '../hooks/useWebSocket';

const BatchProgress = ({ isVisible, onComplete }) => {
  const { isConnected, messages } = useWebSocket('ws://localhost:8000/ws/batch-progress');
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [processingSpeed, setProcessingSpeed] = useState(0);
  const [currentBatch, setCurrentBatch] = useState(0);
  const [totalBatches, setTotalBatches] = useState(0);
  const [circuitBreakerOpen, setCircuitBreakerOpen] = useState(false);

  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];

      if (latestMessage.type === 'progress') {
        setProgress(latestMessage.data.percent_complete);
        setTimeRemaining(latestMessage.data.estimated_time_remaining);
        setProcessingSpeed(latestMessage.data.items_per_second);
        setCurrentBatch(latestMessage.data.current_batch);
        setTotalBatches(latestMessage.data.total_batches);
      } else if (latestMessage.type === 'complete') {
        onComplete();
      } else if (latestMessage.type === 'error') {
        setCircuitBreakerOpen(latestMessage.data.error_code === 'CIRCUIT_BREAKER_OPEN');
      }
    }
  }, [messages, onComplete]);

  return (
    <div className={`batch-progress ${isVisible ? 'visible' : 'hidden'}`}>
      <h3>Processing Reviews</h3>
      <div className="progress-bar">
        <div className="progress" style={{ width: `${progress}%` }}></div>
      </div>
      <div className="progress-stats">
        <div>Progress: {progress.toFixed(1)}%</div>
        <div>Batch: {currentBatch} of {totalBatches}</div>
        <div>Processing speed: {processingSpeed.toFixed(1)} items/sec</div>
        {timeRemaining && <div>Time remaining: {formatTime(timeRemaining)}</div>}
        {circuitBreakerOpen && (
          <div className="circuit-breaker-warning">
            API rate limit reached. Using local processing.
          </div>
        )}
      </div>
    </div>
  );
};
```

This component shows:
- Progress bar with completion percentage
- Current batch and total batches
- Items processed and total items
- Processing speed (items per second)
- Estimated time remaining
- Circuit breaker status (when API rate limits are hit)
- Connection status indicator

## Configuration Options

The batch processing system can be configured through environment variables:

- `BATCH_SIZE_MULTIPLIER`: Adjust all batch sizes (default: 1.0)
- `CIRCUIT_BREAKER_TIMEOUT`: Time before resetting circuit (default: 300 seconds)
- `GEMINI_SLOW_THRESHOLD`: Threshold for slow processing detection (default: 5 seconds)
- `MAX_WORKERS`: Maximum number of parallel workers (default: 4)
- `PARALLEL_PROCESSING`: Enable parallel processing (default: True)
- `ENABLE_WEBSOCKETS`: Enable WebSocket support (default: True)
- `GEMINI_BATCH_SIZE`: Number of reviews to process in each Gemini API batch (default: 10)
- `DEBUG`: Enable debug mode with additional logging (default: False)

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
