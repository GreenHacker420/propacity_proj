// Environment configuration
const environment = {
  // API URL
  apiUrl: 'http://localhost:8000',

  // WebSocket URL - directly use the backend URL
  wsUrl: 'ws://localhost:8000',

  // Environment (development, production, etc.)
  nodeEnv: import.meta.env.MODE || 'development',
};

export default environment;
