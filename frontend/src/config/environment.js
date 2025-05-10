// Environment configuration
const environment = {
 
apiUrl: import.meta.env.VITE_API_URL || '/api',

wsUrl: (() => {
  // In development, use the environment variable
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  
  // In production, construct the URL based on the current location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/ws`;
})(),

// Environment (development, production, etc.)
  nodeEnv: import.meta.env.MODE || 'development',
};

export default environment;
