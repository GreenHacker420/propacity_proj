import React, { useState, useEffect } from 'react';
import BatchProgress from './BatchProgress';

/**
 * Component that displays batch progress (modified to work without WebSockets)
 *
 * @param {Object} props Component props
 * @param {boolean} props.isProcessing Whether processing is active
 * @param {function} props.onComplete Callback when processing is complete
 */
const WebSocketBatchProgress = ({ isProcessing, onComplete }) => {
  const [status, setStatus] = useState(null);
  const [connected, setConnected] = useState(false);

  // Mock WebSocket functionality
  useEffect(() => {
    if (isProcessing) {
      console.log('WebSocketBatchProgress: Processing started');
      
      // Simulate connection established
      setConnected(true);
      
      // Simulate initial status
      setStatus({
        type: 'batch_progress',
        current_batch: 1,
        total_batches: 5,
        items_processed: 0,
        total_items: 100,
        progress_percentage: 0,
        estimated_time_remaining: 30,
        avg_speed: 3.3
      });
      
      // Simulate progress updates
      const interval = setInterval(() => {
        setStatus(prev => {
          if (!prev) return null;
          
          // Calculate new values
          const newItemsProcessed = Math.min(prev.total_items, prev.items_processed + 5);
          const newPercentage = Math.min(100, (newItemsProcessed / prev.total_items) * 100);
          const newTimeRemaining = prev.estimated_time_remaining > 0 ? 
            Math.max(0, prev.estimated_time_remaining - 1) : 0;
          
          // Create updated status
          const newStatus = {
            ...prev,
            items_processed: newItemsProcessed,
            progress_percentage: newPercentage,
            estimated_time_remaining: newTimeRemaining
          };
          
          // If we've reached 100%, trigger completion after a delay
          if (newPercentage >= 100 && onComplete) {
            setTimeout(() => {
              onComplete();
              setStatus(null);
            }, 1000);
          }
          
          return newStatus;
        });
      }, 1000);
      
      // Cleanup function
      return () => {
        clearInterval(interval);
        console.log('WebSocketBatchProgress: Component unmounted');
      };
    } else {
      // Reset status when not processing
      setStatus(null);
      setConnected(false);
    }
  }, [isProcessing, onComplete]);

  // If processing but no status yet, show connecting message
  if (isProcessing && !status) {
    // Log to help with debugging
    console.log('Batch processing started, waiting for updates...');

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-blue-700">Batch Processing Started</p>
        </div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-blue-600">Initializing progress tracking...</p>
        </div>
        <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '30%' }}></div>
        </div>
      </div>
    );
  }

  return (
    <BatchProgress
      status={status}
      isVisible={isProcessing && status !== null}
      onComplete={onComplete}
    />
  );
};

export default WebSocketBatchProgress;
