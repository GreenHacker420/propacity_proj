import React, { useState, useEffect } from 'react';
import { initWebSocket, addMessageHandler, isConnected } from '../services/websocketService';
import BatchProgress from './BatchProgress';

/**
 * Component that connects to WebSocket and displays batch progress
 *
 * @param {Object} props Component props
 * @param {boolean} props.isProcessing Whether processing is active
 * @param {function} props.onComplete Callback when processing is complete
 */
const WebSocketBatchProgress = ({ isProcessing, onComplete }) => {
  const [status, setStatus] = useState(null);
  const [connected, setConnected] = useState(false);

  // Initialize WebSocket connection when component mounts
  useEffect(() => {
    if (isProcessing) {
      // Initialize WebSocket connection
      initWebSocket();

      // Check connection status
      const checkConnection = () => {
        const connectionStatus = isConnected();
        setConnected(connectionStatus);
        return connectionStatus;
      };

      // Try to connect if not already connected
      if (!checkConnection()) {
        const interval = setInterval(() => {
          if (checkConnection()) {
            clearInterval(interval);
          }
        }, 1000);

        // Clean up interval
        return () => clearInterval(interval);
      }
    }
  }, [isProcessing]);

  // Add message handler for batch progress updates
  useEffect(() => {
    if (isProcessing) {
      // Add handler for batch progress messages
      const removeHandler = addMessageHandler((data) => {
        if (data.type === 'batch_progress') {
          console.log('Received batch progress update:', data);
          setStatus(data);
        }
      });

      // Clean up handler when component unmounts
      return () => removeHandler();
    } else {
      // Reset status when not processing
      setStatus(null);
    }
  }, [isProcessing]);

  // Handle completion
  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    }
  };

  // If processing but no status yet, show connecting message
  if (isProcessing && !status) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-blue-700">Connecting to real-time progress updates...</p>
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
      onComplete={handleComplete}
    />
  );
};

export default WebSocketBatchProgress;
