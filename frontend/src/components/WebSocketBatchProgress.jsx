import React, { useState, useEffect, useRef } from 'react';
import BatchProgress from './BatchProgress';
import { addMessageHandler, removeMessageHandler, isConnected, initWebSocket } from '../services/websocketService';

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
  const [connectionAttempted, setConnectionAttempted] = useState(false);
  const messageHandlerRef = useRef(null);
  const removeHandlerRef = useRef(null);

  // Initialize WebSocket connection if needed
  useEffect(() => {
    if (isProcessing && !connectionAttempted) {
      console.log('WebSocketBatchProgress: Ensuring WebSocket connection is established');
      initWebSocket();
      setConnectionAttempted(true);
    }
  }, [isProcessing, connectionAttempted]);

  // Set up message handler for WebSocket messages
  useEffect(() => {
    if (isProcessing) {
      console.log('WebSocketBatchProgress: Processing started');

      // Check if WebSocket is connected
      const isWsConnected = isConnected();
      setConnected(isWsConnected);
      console.log('WebSocket connection status:', isWsConnected ? 'Connected' : 'Disconnected');

      // Define message handler function
      const handleMessage = (message) => {
        console.log('WebSocket message received in component:', message);

        // Only process batch_progress messages
        if (message && message.type === 'batch_progress') {
          console.log('Setting batch progress status:', message);
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

      // Store the handler in a ref to prevent recreating it on each render
      messageHandlerRef.current = handleMessage;

      // Add message handler only once
      if (!removeHandlerRef.current) {
        removeHandlerRef.current = addMessageHandler(handleMessage);
        console.log('Added WebSocket message handler');
      }

      // Listen for WebSocket connection status changes
      const handleConnectionChange = () => {
        const newConnected = isConnected();
        console.log('WebSocket connection changed:', newConnected ? 'Connected' : 'Disconnected');
        setConnected(newConnected);
      };

      window.addEventListener('websocketStatusChange', handleConnectionChange);

      // Cleanup function
      return () => {
        // Only remove the handler when the component is truly unmounting
        if (removeHandlerRef.current) {
          console.log('WebSocketBatchProgress: Removing message handler');
          removeHandlerRef.current();
          removeHandlerRef.current = null;
        }
        window.removeEventListener('websocketStatusChange', handleConnectionChange);
      };
    }
  }, [isProcessing, onComplete]);

  // Reset status when not processing
  useEffect(() => {
    if (!isProcessing) {
      setStatus(null);
    }
  }, [isProcessing]);

  // If processing but no status yet, show connecting message
  if (isProcessing && !status) {
    // Log to help with debugging
    console.log('Batch processing started, waiting for updates...');

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-blue-700">Batch Processing Started</p>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
            connected ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
          }`}>
            {connected ? "Connected" : "Connecting..."}
          </span>
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
