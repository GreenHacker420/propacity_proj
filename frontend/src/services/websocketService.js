// Import environment configuration
import environment from '../config/environment';

// WebSocket connection management
let socket = null;
let connectionStatus = false;
let reconnectAttempts = 0;
let pingInterval = null;
const MAX_RECONNECT_ATTEMPTS = 5; // Increased from 3 to 5
const RECONNECT_DELAY = 2000; // 2 seconds
const messageHandlers = [];

// Dispatch connection status change event
const dispatchConnectionStatusChange = (status) => {
  const event = new CustomEvent('websocketStatusChange', { detail: { connected: status } });
  window.dispatchEvent(event);
  console.log(`WebSocket connection status changed to: ${status ? 'connected' : 'disconnected'}`);
};

// Initialize WebSocket connection
export const initWebSocket = () => {
  // If already connected, don't create a new connection
  if (socket && socket.readyState === WebSocket.OPEN) {
    console.log('WebSocket already connected, reusing existing connection');
    return socket;
  }

  // If connecting, don't create a new connection
  if (socket && socket.readyState === WebSocket.CONNECTING) {
    console.log('WebSocket already connecting, waiting for connection');
    return socket;
  }

  try {
    // Clean up any existing socket
    if (socket) {
      try {
        socket.close();
      } catch (e) {
        console.error('Error closing existing socket:', e);
      }
    }

    // Clear any existing ping interval
    if (pingInterval) {
      clearInterval(pingInterval);
      pingInterval = null;
    }

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
      dispatchConnectionStatusChange(true);

      // Send a ping to keep the connection alive
      pingInterval = setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          try {
            socket.send(JSON.stringify({ type: 'ping' }));
          } catch (error) {
            console.error('Error sending ping:', error);
            // If ping fails, try to reconnect
            closeWebSocket();
            initWebSocket();
          }
        }
      }, 30000); // Send ping every 30 seconds

      // Send an initial message to confirm connection
      try {
        socket.send(JSON.stringify({ type: 'client_connected' }));
      } catch (error) {
        console.error('Error sending initial message:', error);
      }
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
        } else if (data.type === 'pong') {
          console.log('Received pong from server');
        }

        // Call all registered message handlers
        if (messageHandlers.length > 0) {
          console.log(`Calling ${messageHandlers.length} message handlers`);
          messageHandlers.forEach(handler => {
            try {
              handler(data);
            } catch (error) {
              console.error('Error in message handler:', error);
            }
          });
        } else {
          console.log('No message handlers registered');
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onclose = (event) => {
      console.log(`WebSocket connection closed with code ${event.code}`);
      connectionStatus = false;
      dispatchConnectionStatusChange(false);

      // Clear ping interval
      if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
      }

      // Attempt to reconnect
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
        setTimeout(initWebSocket, RECONNECT_DELAY); // Try to reconnect after delay
      } else {
        console.log('Maximum reconnection attempts reached. WebSocket will remain disconnected.');
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      // Don't set connectionStatus to false here, let onclose handle it
    };

    return socket;
  } catch (error) {
    console.error('Error initializing WebSocket:', error);
    connectionStatus = false;
    dispatchConnectionStatusChange(false);
    return null;
  }
};

// Initialize WebSocket when the service is loaded
// We'll initialize on demand instead of immediately
console.log('WebSocket service loaded, will connect when needed');

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
