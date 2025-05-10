// Mock WebSocket implementation for environments where WebSockets are not available
const createMockWebSocket = () => {
  console.log('Creating mock WebSocket - real WebSockets are disabled');
  
  // Create a mock socket object
  const mockSocket = {
    send: (data) => console.log('Mock WebSocket send:', data),
    close: () => console.log('Mock WebSocket closed'),
    onmessage: null,
    onopen: null,
    onclose: null,
    onerror: null,
    readyState: 1, // WebSocket.OPEN
  };
  
  // Simulate connection open event
  setTimeout(() => {
    if (mockSocket.onopen) {
      console.log('Mock WebSocket: Connection opened');
      mockSocket.onopen({ type: 'open' });
    }
  }, 100);
  
  return mockSocket;
};

// WebSocket connection management
let socket = null;
let connectionStatus = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;
const messageHandlers = [];

// Initialize WebSocket connection
export const initWebSocket = () => {
  try {
    // Use mock WebSocket instead of real one
    socket = createMockWebSocket();
    
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
// Initialize WebSocket when the service is loaded
let initializedSocket = null;
try {
  initializedSocket = initWebSocket();
  
  // Simulate batch progress updates for testing
  if (initializedSocket) {
    console.log('Setting up mock progress updates simulation');
    
    // Wait a bit before starting the simulation
    setTimeout(() => {
      // Initial mock progress data
      const mockProgressData = {
        type: 'batch_progress',
        current_batch: 1,
        total_batches: 5,
        batch_time: 2.3,
        items_processed: 20,
        total_items: 100,
        avg_speed: 8.7,
        estimated_time_remaining: 9.2,
        progress_percentage: 20
      };
      
      console.log('Sending first mock progress update:', mockProgressData);
      
      // Call all registered message handlers with the mock data
      messageHandlers.forEach(handler => {
        try {
          handler(mockProgressData);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
      
      // Simulate more updates
      const interval = setInterval(() => {
        // Update the progress data
        mockProgressData.items_processed += 20;
        mockProgressData.progress_percentage += 20;
        mockProgressData.estimated_time_remaining = Math.max(0, mockProgressData.estimated_time_remaining - 2);
        
        console.log('Sending mock progress update:', mockProgressData);
        
        // Call all registered message handlers with the updated mock data
        messageHandlers.forEach(handler => {
          try {
            handler({...mockProgressData});
          } catch (error) {
            console.error('Error in message handler:', error);
          }
        });
        
        // Stop after reaching 100%
        if (mockProgressData.progress_percentage >= 100) {
          console.log('Mock progress updates complete');
          clearInterval(interval);
        }
      }, 2000); // Update every 2 seconds
    }, 3000); // Start after 3 seconds
  }
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
