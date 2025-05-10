import React, { useState, useEffect } from 'react';
import BatchProgress from './BatchProgress';
import { addMessageHandler, removeMessageHandler, isConnected } from '../services/websocketService';

/**
 * Component that displays batch progress using WebSockets
 *
 * @param {Object} props Component props
 * @param {boolean} props.isProcessing Whether processing is active
 * @param {function} props.onComplete Callback when processing is complete
 */
const WebSocketBatchProgress = ({ isProcessing, onComplete }) => {
  const [status, setStatus] = useState(null);
  const [connected, setConnected] = useState(false);

  // Use real WebSocket functionality
  useEffect(() => {
    if (isProcessing) {
      console.log('WebSocketBatchProgress: Processing started');

      // Check if WebSocket is connected
      setConnected(isConnected());

      // Set up message handler for WebSocket messages
      const handleMessage = (message) => {
        console.log('WebSocket message received in component:', message);

        // Only process batch_progress messages
        if (message.type === 'batch_progress') {
          setStatus(message);

          // If we've reached 100%, trigger completion after a delay
          if (message.progress_percentage >= 100 && onComplete) {
            setTimeout(() => {
              onComplete();
              setStatus(null);
            }, 1000);
          }
        }
      };

      // Add message handler
      const removeHandler = addMessageHandler(handleMessage);

      // Listen for WebSocket connection status changes
      const handleConnectionChange = () => {
        setConnected(isConnected());
      };

      window.addEventListener('websocketStatusChange', handleConnectionChange);

      // Cleanup function
      return () => {
        removeHandler();
        window.removeEventListener('websocketStatusChange', handleConnectionChange);
        console.log('WebSocketBatchProgress: Component unmounted');
      };
    } else {
      // Reset status when not processing
      setStatus(null);
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
