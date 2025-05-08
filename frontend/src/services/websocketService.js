import { getToken } from './authService';
import environment from '../config/environment';

let socket = null;
let messageHandlers = [];
let reconnectTimer = null;
let isConnecting = false;

/**
 * Initialize WebSocket connection
 */
export const initWebSocket = () => {
  if (socket || isConnecting) return;

  // Use a mock token for development
  const mockToken = 'dev_token_123';

  isConnecting = true;

  // Get the base URL from environment config
  const wsUrl = environment.wsUrl;

  // Log connection attempt
  console.log('Connecting to WebSocket at:', `${wsUrl}/ws?token=${mockToken}`);

  // Create WebSocket connection with mock token
  try {
    socket = new WebSocket(`${wsUrl}/ws?token=${mockToken}`);

    // Log connection status to help with debugging
    console.log('WebSocket connection created, waiting for open event...');

    socket.onopen = () => {
      console.log('WebSocket connection established');
      isConnecting = false;

      // Clear reconnect timer if it exists
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      // Send ping every 30 seconds to keep connection alive
      setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle pong message
        if (data.type === 'pong') {
          return;
        }

        // Notify all handlers
        messageHandlers.forEach(handler => {
          try {
            handler(data);
          } catch (error) {
            console.error('Error in WebSocket message handler:', error);
          }
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onclose = (event) => {
      console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
      socket = null;
      isConnecting = false;

      // Attempt to reconnect after 5 seconds
      if (!reconnectTimer) {
        reconnectTimer = setTimeout(() => {
          reconnectTimer = null;
          initWebSocket();
        }, 5000);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      isConnecting = false;
    };
  } catch (error) {
    console.error('Error creating WebSocket connection:', error);
    isConnecting = false;
  }
};

/**
 * Close WebSocket connection
 */
export const closeWebSocket = () => {
  if (socket) {
    socket.close();
    socket = null;
  }

  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  messageHandlers = [];
};

/**
 * Add message handler
 * @param {function} handler Function to handle WebSocket messages
 * @returns {function} Function to remove the handler
 */
export const addMessageHandler = (handler) => {
  if (typeof handler !== 'function') {
    console.error('WebSocket message handler must be a function');
    return () => {};
  }

  messageHandlers.push(handler);

  // Return function to remove handler
  return () => {
    messageHandlers = messageHandlers.filter(h => h !== handler);
  };
};

/**
 * Get WebSocket connection status
 * @returns {boolean} True if connected, false otherwise
 */
export const isConnected = () => {
  return socket !== null && socket.readyState === WebSocket.OPEN;
};

/**
 * Initialize WebSocket when user logs in
 */
export const initWebSocketOnLogin = () => {
  // Close existing connection if any
  closeWebSocket();

  // Initialize new connection
  initWebSocket();
};

/**
 * Close WebSocket when user logs out
 */
export const closeWebSocketOnLogout = () => {
  closeWebSocket();
};
