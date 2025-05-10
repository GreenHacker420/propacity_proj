import React, { useState, useEffect, useRef } from 'react';

/**
 * Component to display batch processing progress
 *
 * @param {Object} props Component props
 * @param {Object} props.status Batch processing status
 * @param {boolean} props.isVisible Whether the component is visible
 * @param {function} props.onComplete Callback when processing is complete
 */
const BatchProgress = ({ status, isVisible, onComplete }) => {
  const [timeRemaining, setTimeRemaining] = useState('');
  const [progressPercentage, setProgressPercentage] = useState(0);
  const lastStatusRef = useRef(null);

  // Update time remaining and progress percentage when status changes
  useEffect(() => {
    if (!status) return;

    // Store the latest valid status
    lastStatusRef.current = status;

    // Format time remaining
    if (status.estimated_time_remaining) {
      const seconds = Math.round(status.estimated_time_remaining);
      if (seconds < 60) {
        setTimeRemaining(`${seconds} seconds`);
      } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        setTimeRemaining(`${minutes} min ${remainingSeconds} sec`);
      }
    }

    // Calculate progress percentage
    const percentage = status.progress_percentage !== undefined ? status.progress_percentage :
      (status.items_processed !== undefined && status.total_items !== undefined && status.total_items > 0)
        ? Math.min(100, (status.items_processed / status.total_items) * 100)
        : (status.current_batch !== undefined && status.total_batches !== undefined && status.total_batches > 0)
          ? Math.min(100, (status.current_batch / status.total_batches) * 100)
          : 0;

    setProgressPercentage(percentage);

    // Log progress update
    console.log(`Batch progress updated: ${percentage.toFixed(1)}%`);

    // Call onComplete when processing is done
    if (percentage >= 100 && onComplete) {
      // Add a small delay to show 100% before completing
      setTimeout(() => {
        onComplete();
      }, 1000);
    }
  }, [status, onComplete]);

  // If not visible or no status (and no previous status), don't render
  if (!isVisible || (!status && !lastStatusRef.current)) {
    return null;
  }

  // Use the current status or the last valid status if current is null
  const displayStatus = status || lastStatusRef.current;

  return (
    <div
      className="p-4 border border-gray-200 rounded-lg shadow-md bg-white mb-4"
    >
      <div className="flex justify-between items-center mb-2">
        <p className="font-bold text-gray-800">Batch Processing</p>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          progressPercentage < 100
            ? "bg-blue-100 text-blue-800"
            : "bg-green-100 text-green-800"
        }`}>
          {progressPercentage < 100 ? "Processing" : "Complete"}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-md h-2 mb-2">
        <div
          className={`h-full rounded-md ${progressPercentage < 100 ? "bg-blue-500" : "bg-green-500"} ${
            progressPercentage < 100 ? "animate-pulse" : ""
          }`}
          style={{ width: `${Math.max(5, progressPercentage)}%` }}
        ></div>
      </div>

      <div className="flex justify-between text-sm text-gray-600">
        <p>
          {displayStatus.items_processed || 0} / {displayStatus.total_items || 0} items
          {displayStatus.avg_speed ? ` (${displayStatus.avg_speed.toFixed(1)} items/sec)` : ''}
        </p>
        {timeRemaining && progressPercentage < 100 && (
          <p>Est. time remaining: {timeRemaining}</p>
        )}
      </div>

      {displayStatus.current_batch && displayStatus.total_batches && (
        <p className="text-xs text-gray-500 mt-1">
          Batch {displayStatus.current_batch} of {displayStatus.total_batches}
          {displayStatus.batch_time ? ` (${displayStatus.batch_time.toFixed(1)}s per batch)` : ''}
        </p>
      )}
    </div>
  );
};

export default BatchProgress;
