import React, { useState, useEffect } from 'react';

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

  useEffect(() => {
    // Format time remaining
    if (status && status.estimated_time_remaining) {
      const seconds = Math.round(status.estimated_time_remaining);
      if (seconds < 60) {
        setTimeRemaining(`${seconds} seconds`);
      } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        setTimeRemaining(`${minutes} min ${remainingSeconds} sec`);
      }
    }

    // Call onComplete when processing is done
    if (status && status.progress_percentage === 100 && onComplete) {
      // Add a small delay to show 100% before completing
      setTimeout(() => {
        onComplete();
      }, 1000);
    }
  }, [status, onComplete]);

  if (!isVisible || !status) {
    return null;
  }

  return (
    <div
      className="p-4 border border-gray-200 rounded-lg shadow-md bg-white mb-4"
    >
      <div className="flex justify-between items-center mb-2">
        <p className="font-bold text-gray-800">Processing Reviews</p>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
          status.progress_percentage < 100
            ? "bg-blue-100 text-blue-800"
            : "bg-green-100 text-green-800"
        }`}>
          {status.progress_percentage < 100 ? "Processing" : "Complete"}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-md h-2 mb-2">
        <div
          className={`h-full rounded-md ${status.progress_percentage < 100 ? "bg-blue-500" : "bg-green-500"} ${
            status.progress_percentage < 100 ? "animate-pulse" : ""
          }`}
          style={{ width: `${status.progress_percentage}%` }}
        ></div>
      </div>

      <div className="flex justify-between text-sm text-gray-600">
        <p>
          {status.items_processed} / {status.total_items} items
          {status.avg_speed ? ` (${status.avg_speed.toFixed(1)} items/sec)` : ''}
        </p>
        {timeRemaining && status.progress_percentage < 100 && (
          <p>Est. time remaining: {timeRemaining}</p>
        )}
      </div>

      {status.current_batch && status.total_batches && (
        <p className="text-xs text-gray-500 mt-1">
          Batch {status.current_batch} of {status.total_batches}
          {status.batch_time ? ` (${status.batch_time.toFixed(1)}s per batch)` : ''}
        </p>
      )}
    </div>
  );
};

export default BatchProgress;
