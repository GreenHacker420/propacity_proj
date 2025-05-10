import { useState, useEffect } from 'react';
import api from '../services/api';

/**
 * Custom hook for fetching and managing Gemini API status
 * @param {number} refreshInterval - Interval in milliseconds to refresh the status
 * @returns {Object} Gemini status state and functions
 */
const useGeminiStatus = (refreshInterval = 10000) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState({
    rateLimit: 0,
    circuit: 0
  });

  // Fetch Gemini status
  const fetchStatus = async () => {
    try {
      setError(null);
      const geminiStatus = await api.getGeminiStatus();
      setStatus(geminiStatus);

      // Set time remaining
      setTimeRemaining({
        rateLimit: geminiStatus.rate_limit_reset_in || 0,
        circuit: geminiStatus.circuit_reset_in || 0
      });
    } catch (error) {
      console.error('Error fetching Gemini status:', error);
      setError(error);
      
      // Set a default status when the endpoint is not available
      setStatus({
        available: false,
        model: 'unavailable',
        rate_limited: false,
        circuit_open: false,
        using_local_processing: true
      });
    } finally {
      setLoading(false);
    }
  };

  // Update countdown timers
  useEffect(() => {
    if (!status) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => ({
        rateLimit: Math.max(0, prev.rateLimit - 1),
        circuit: Math.max(0, prev.circuit - 1)
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, [status]);

  // Fetch status on mount and periodically
  useEffect(() => {
    fetchStatus();

    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // Format time remaining
  const formatTime = (seconds) => {
    if (!seconds) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return {
    status,
    loading,
    error,
    timeRemaining,
    fetchStatus,
    formatTime,
    isLimited: status?.rate_limited || status?.circuit_open || !status?.available
  };
};

export default useGeminiStatus;
