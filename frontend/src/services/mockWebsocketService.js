// Mock WebSocket connection management
let connectionStatus = false;
const messageHandlers = [];

// Dispatch connection status change event
const dispatchConnectionStatusChange = (status) => {
  const event = new CustomEvent('websocketStatusChange', { detail: { connected: status } });
  window.dispatchEvent(event);
  console.log(`Mock WebSocket connection status changed to: ${status ? 'connected' : 'disconnected'}`);
};

// Initialize WebSocket connection
export const initWebSocket = () => {
  console.log('Initializing mock WebSocket service');
  
  // Simulate a successful connection
  setTimeout(() => {
    connectionStatus = true;
    dispatchConnectionStatusChange(true);
    console.log('Mock WebSocket connection established');
    
    // Send a welcome message to simulate server response
    const welcomeMessage = {
      type: 'connection_established',
      message: 'Mock WebSocket connection established successfully',
      user_id: 'mock_user'
    };
    
    // Notify all handlers
    messageHandlers.forEach(handler => {
      try {
        handler(welcomeMessage);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }, 500);
  
  return {};
};

// Close WebSocket connection
export const closeWebSocket = () => {
  console.log('Closing mock WebSocket connection');
  connectionStatus = false;
  dispatchConnectionStatusChange(false);
};

// Send a message (mock implementation)
export const sendWebSocketMessage = (message) => {
  console.log('Mock sending WebSocket message:', message);
  
  // Simulate a response for batch progress
  if (message.type === 'start_batch_processing') {
    simulateBatchProgress();
  }
};

// Add a message handler
export const addMessageHandler = (handler) => {
  messageHandlers.push(handler);
  return () => {
    const index = messageHandlers.indexOf(handler);
    if (index !== -1) {
      messageHandlers.splice(index, 1);
    }
  };
};

// Simulate batch progress
const simulateBatchProgress = () => {
  const totalBatches = 10;
  const totalItems = 100;
  let currentBatch = 0;
  let itemsProcessed = 0;
  
  const interval = setInterval(() => {
    currentBatch++;
    itemsProcessed += 10;
    
    const status = {
      type: 'batch_progress',
      current_batch: currentBatch,
      total_batches: totalBatches,
      batch_time: 0.5,
      items_processed: itemsProcessed,
      total_items: totalItems,
      avg_speed: 20,
      estimated_time_remaining: (totalBatches - currentBatch) * 0.5,
      progress_percentage: (itemsProcessed / totalItems) * 100
    };
    
    // Notify all handlers
    messageHandlers.forEach(handler => {
      try {
        handler(status);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
    
    if (currentBatch >= totalBatches) {
      clearInterval(interval);
      
      // Send completion message
      const completionMessage = {
        type: 'batch_complete',
        message: 'Batch processing completed successfully'
      };
      
      // Notify all handlers
      messageHandlers.forEach(handler => {
        try {
          handler(completionMessage);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }, 500);
};

// Get connection status
export const getConnectionStatus = () => connectionStatus;
