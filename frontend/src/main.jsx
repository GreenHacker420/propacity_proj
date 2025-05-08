import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { initWebSocket } from './services/websocketService'
import './services/authService' // Import to ensure auth token is initialized

// No need for process.env polyfill anymore

// Initialize WebSocket connection with a small delay to ensure environment is loaded
setTimeout(() => {
  console.log('Initializing WebSocket connection from main.jsx');
  initWebSocket();
}, 500);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)