/**
 * Authentication service for handling tokens
 */

// Token storage key
const TOKEN_KEY = 'auth_token';

/**
 * Get the authentication token from local storage
 * @returns {string|null} The authentication token or null if not found
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Set the authentication token in local storage
 * @param {string} token The authentication token to store
 */
export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Remove the authentication token from local storage
 */
export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Check if the user is authenticated
 * @returns {boolean} True if the user is authenticated, false otherwise
 */
export const isAuthenticated = () => {
  return getToken() !== null;
};

/**
 * Get a mock token for development
 * @returns {string} A mock token
 */
export const getMockToken = () => {
  // This is a mock token for development purposes only
  return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJpZCI6IjEyMzQ1Njc4OTAiLCJpYXQiOjE1MTYyMzkwMjJ9.L8i6g3PfcHlioHCCPURC9pmXT7gdJpx3kOoyAfNUwCc';
};

// For development, set a mock token if none exists
if (!getToken() && (import.meta.env.MODE === 'development' || import.meta.env.DEV)) {
  setToken(getMockToken());
}

export default {
  getToken,
  setToken,
  removeToken,
  isAuthenticated,
  getMockToken
};
