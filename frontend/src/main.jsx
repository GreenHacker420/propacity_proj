import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import environment from './config/environment'

// We'll initialize the WebSocket connection on demand in the components
// rather than at application startup to avoid unnecessary connections
console.log('Application starting with environment:', environment.nodeEnv);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)