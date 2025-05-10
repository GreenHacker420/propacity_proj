// Import environment configuration
import environment from '../config/environment';

// WebSocket connection management
let socket = null;
let connectionStatus = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;
const messageHandlers = [];

// Initialize WebSocket connection
export const initWebSocket = () => {
  try {
    // Get WebSocket URL from environment
    const wsUrl = environment.wsUrl;
    console.log(`Connecting to WebSocket at: ${wsUrl}`);

    // Create real WebSocket connection
    socket = new WebSocket(wsUrl);

    // Set up event handlers
    socket.onopen = (event) => {
      console.log('WebSocket connection established');
      connectionStatus = true;
      reconnectAttempts = 0;

      // Send a ping to keep the connection alive
      setInterval(() => {
        if (connectionStatus) {
          try {
            socket.send(JSON.stringify({ type: 'ping' }));
          } catch (error) {
            console.error('Error sending ping:', error);
          }
        }
      }, 30000); // Send ping every 30 seconds
    };

    socket.onmessage = (event) => {
      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        console.log('WebSocket message received:', data);

        // Handle different message types
        if (data.type === 'batch_progress') {
          // Update progress information
          const progressEvent = new CustomEvent('batchProgress', { detail: data });
          window.dispatchEvent(progressEvent);
        } else if (data.type === 'connection_established') {
          console.log('WebSocket connection confirmed by server');
        }

        // Call all registered message handlers
        messageHandlers.forEach(handler => {
          try {
            handler(data);
          } catch (error) {
            console.error('Error in message handler:', error);
          }
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed');
      connectionStatus = false;

      // Attempt to reconnect
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
        setTimeout(initWebSocket, 3000); // Try to reconnect after 3 seconds
      } else {
        console.log('Maximum reconnection attempts reached. WebSocket will remain disconnected.');
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return socket;
  } catch (error) {
    console.error('Error initializing WebSocket:', error);
    return null;
  }
};

// Initialize WebSocket when the service is loaded
let initializedSocket = null;
try {
  initializedSocket = initWebSocket();
  console.log('WebSocket initialized:', initializedSocket ? 'success' : 'failed');
} catch (error) {
  console.error('Failed to initialize WebSocket:', error);
}

// Export functions for sending messages
export const sendWebSocketMessage = (message) => {
  if (socket && connectionStatus) {
    try {
      socket.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
    }
  } else {
    console.warn('Cannot send message: WebSocket is not connected');
  }
};

// Add a message handler
// Add a message handler
export const addMessageHandler = (handler) => {
  if (typeof handler === 'function') {
    messageHandlers.push(handler);
    // Return a function to remove this handler
    return () => removeMessageHandler(handler);
  }
  // Return a no-op function if handler is invalid
  return () => {};
};

// Remove a message handler
export const removeMessageHandler = (handler) => {
  const index = messageHandlers.indexOf(handler);
  if (index !== -1) {
    messageHandlers.splice(index, 1);
    return true;
  }
  return false;
};

// Export connection status
export const getWebSocketStatus = () => ({
  isConnected: connectionStatus,
  reconnectAttempts,
});

// Check if connected
export const isConnected = () => connectionStatus;

// Export close function
export const closeWebSocket = () => {
  if (socket) {
    socket.close();
    socket = null;
    connectionStatus = false;
  }
};

// Default export for backward compatibility
export default {
  initWebSocket,
  sendWebSocketMessage,
  addMessageHandler,
  removeMessageHandler,
  getWebSocketStatus,
  isConnected,
  closeWebSocket
};
