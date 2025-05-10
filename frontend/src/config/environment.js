// Environment configuration
const environment = {
  // API URL from environment or default to /api
  apiUrl: import.meta.env.VITE_API_URL || '/api',

  // WebSocket URL construction
  wsUrl: (() => {
    // In development, use the environment variable if available
    if (import.meta.env.VITE_WS_URL) {
      console.log(`Using WebSocket URL from env: ${import.meta.env.VITE_WS_URL}`);
      return import.meta.env.VITE_WS_URL;
    }

    // In production or if no env var, construct the URL based on the current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;
    console.log(`Constructed WebSocket URL: ${wsUrl}`);
    return wsUrl;
  })(),

  // Environment (development, production, etc.)
  nodeEnv: import.meta.env.MODE || 'development',

  // Debug flag
  debug: import.meta.env.VITE_DEBUG === 'true' || false,
};

// Log environment configuration in development
if (environment.nodeEnv === 'development' || environment.debug) {
  console.log('Environment configuration:', {
    apiUrl: environment.apiUrl,
    wsUrl: environment.wsUrl,
    nodeEnv: environment.nodeEnv,
  });
}

export default environment;
