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
    // Use /ws endpoint instead of /public-ws to match nginx configuration
    const wsUrl = `${protocol}//${host}/ws`;
    console.log(`Constructed WebSocket URL: ${wsUrl}`);
    return wsUrl;
  })(),

  // Public WebSocket URL construction
  publicWsUrl: (() => {
    // In development, use the environment variable if available
    if (import.meta.env.VITE_PUBLIC_WS_URL) {
      console.log(`Using Public WebSocket URL from env: ${import.meta.env.VITE_PUBLIC_WS_URL}`);
      return import.meta.env.VITE_PUBLIC_WS_URL;
    }

    // In production or if no env var, construct the URL based on the current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    // Use /ws endpoint instead of /public-ws to match nginx configuration
    const publicWsUrl = `${protocol}//${host}/ws`;
    console.log(`Constructed Public WebSocket URL: ${publicWsUrl}`);
    return publicWsUrl;
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
    publicWsUrl: environment.publicWsUrl,
    nodeEnv: environment.nodeEnv,
  });
}

export default environment;
