import axios from 'axios';
import { getToken } from './authService';

// Always use the direct backend URL to avoid proxy issues
// In production, we'll add the /api prefix to each endpoint
const baseURL = '';

// Configure axios
axios.defaults.baseURL = baseURL;
axios.defaults.withCredentials = true;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// API status tracking
let apiStatus = {
  error: null,
  lastErrorTime: null,
  quotaExceeded: false,
  retryAfter: null
};

// Authentication is disabled for now
// No request interceptor for authentication

// List of endpoints that don't require authentication
const noAuthEndpoints = [
  '/api/gemini/status',
  '/api/history',
  '/api/weekly/priorities'
];

// Add request interceptor for authentication
axios.interceptors.request.use(
  config => {
    // Check if this endpoint requires authentication
    const isAuthRequired = !noAuthEndpoints.some(endpoint => config.url.includes(endpoint));

    // Only log auth token for endpoints that require authentication
    if (isAuthRequired) {
      const token = getToken();
      console.log('Auth token for request:', token); // Debug log
      console.log('Request URL:', config.url); // Debug log

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log('Request headers:', config.headers); // Debug log
      } else {
        console.warn('No auth token found for request'); // Debug log

        // For scrape endpoint, add a hardcoded token if no token is found
        if (config.url.includes('/api/scrape')) {
          const hardcodedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJpZCI6IjY4MWMyZWNmZWJjOGQxYjI2MGY3ODIzMyIsImV4cCI6MTc0NjY5MDE3MX0.lPpWE0oRzHjK4RkaNgerzIQS6p5myiV_q7uDo9TVItk';
          config.headers.Authorization = `Bearer ${hardcodedToken}`;
          console.log('Added hardcoded token for scrape endpoint');
        }
      }
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Intercept responses to track API status
axios.interceptors.response.use(
  response => {
    // Clear error state on successful response
    apiStatus.error = null;
    apiStatus.quotaExceeded = false;
    return response;
  },
  error => {
    // Track API errors
    if (error.response) {
      apiStatus.error = error.response.data.detail || error.message;
      apiStatus.lastErrorTime = new Date();

      // Check for quota exceeded errors
      if (error.response.status === 429 ||
          (error.response.data.detail && error.response.data.detail.includes('quota'))) {
        apiStatus.quotaExceeded = true;

        // Try to extract retry-after header or from error message
        const retryAfter = error.response.headers['retry-after'];
        if (retryAfter) {
          apiStatus.retryAfter = parseInt(retryAfter);
        } else if (error.response.data.detail && error.response.data.detail.includes('retry_delay')) {
          // Try to extract from error message
          const match = error.response.data.detail.match(/seconds":\s*(\d+)/);
          if (match && match[1]) {
            apiStatus.retryAfter = parseInt(match[1]);
          }
        }
      }
    } else {
      apiStatus.error = error.message;
      apiStatus.lastErrorTime = new Date();
    }

    return Promise.reject(error);
  }
);

// API service for handling all backend requests
const api = {
  // Get current API status
  getApiStatus: () => {
    return { ...apiStatus };
  },

  // Login to get an authentication token
  login: async (username, password) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('/api/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // Store the token
      if (response.data && response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
      }

      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  // Get Gemini service status
  getGeminiStatus: async () => {
    try {
      // Use a specific configuration to indicate this doesn't need authentication
      const response = await axios.get('/api/gemini/status', {
        headers: {
          // Explicitly remove any Authorization header
          'Authorization': ''
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching Gemini status:', error);
      return {
        available: false,
        model: 'unknown',
        rate_limited: false,
        circuit_open: false,
        using_local_processing: true
      };
    }
  },

  // Upload and analyze a CSV file
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    // Use axios with baseURL configuration
    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        // Explicitly remove any Authorization header
        'Authorization': ''
      }
    });

    return response.data;
  },

  // Scrape and analyze data from online sources
  scrapeData: async (source, query, limit) => {
    const params = {
      source,
      query,
      limit
    };

    console.log('Scraping data with params:', params);

    // No authentication required for scraping
    const response = await axios.get('/api/scrape', { params });

    console.log('Scrape response status:', response.status);
    return response.data;
  },

  // Perform sentiment analysis on a batch of texts
  analyzeSentiment: async (texts) => {
    const response = await axios.post('/api/sentiment/batch', {
      texts: Array.isArray(texts) ? texts : [texts]
    });
    return response.data;
  },

  // Categorize reviews
  categorizeReviews: async (reviews) => {
    const response = await axios.post('/api/categorize', {
      reviews: Array.isArray(reviews) ? reviews : [reviews]
    });
    return response.data;
  },

  // Generate summary from analyzed reviews
  generateSummary: async (reviewsData) => {
    try {
      const response = await axios.post('/api/summary', reviewsData);
      return response.data;
    } catch (error) {
      console.error('Error generating summary:', error);
      throw error;
    }
  },

  // Record processing time
  recordProcessingTime: async (operation, startTime, recordCount, fileName = null, source = null, query = null) => {
    // Calculate duration in seconds
    const endTime = Date.now();
    const durationSeconds = (endTime - startTime) / 1000;

    await axios.post('/api/timing/record', {
      operation,
      file_name: fileName,
      source,
      query,
      record_count: recordCount,
      duration_seconds: durationSeconds
    });

    return durationSeconds;
  },

  // Get estimated processing time
  getEstimatedTime: async (operation, recordCount) => {
    const response = await axios.get(`/api/timing/estimate/${operation}?record_count=${recordCount}`);
    return response.data;
  },

  // Record analysis history
  recordAnalysisHistory: async (sourceType, sourceName, reviewsData, summary) => {
    // Use axios with baseURL configuration
    await axios.post('/api/history', {
      source_type: sourceType,
      source_name: sourceName,
      record_count: reviewsData.length,
      avg_sentiment_score: reviewsData.reduce((sum, review) => sum + review.sentiment_score, 0) / reviewsData.length,
      pain_point_count: reviewsData.filter(review => review.category === 'pain_point').length,
      feature_request_count: reviewsData.filter(review => review.category === 'feature_request').length,
      positive_feedback_count: reviewsData.filter(review => review.category === 'positive_feedback').length,
      summary: summary
    });
  },

  // Download PDF report
  downloadPDF: async (analyzedReviews) => {
    const response = await axios.post('/api/summary/pdf', analyzedReviews, {
      responseType: 'blob'
    });

    // Create a download link for the PDF
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `product_review_summary_${new Date().toISOString().split('T')[0]}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Get prioritized insights from recent feedback
  getPriorityInsights: async (sourceType, timeRange = 'week') => {
    try {
      const response = await axios.get('/api/weekly/priorities', {
        params: {
          source_type: sourceType,
          time_range: timeRange
        },
        headers: {
          // Explicitly remove any Authorization header
          'Authorization': ''
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching insights:', error);
      throw error;
    }
  },

  // Create a weekly summary for a specific source
  createWeeklySummary: async (sourceType, sourceName) => {
    const response = await axios.post('/api/weekly/summary', null, {
      params: { source_type: sourceType, source_name: sourceName }
    });
    return response.data;
  },

  // Get a specific weekly summary by ID
  getWeeklySummary: async (summaryId) => {
    const response = await axios.get(`/api/weekly/summary/${summaryId}`);
    return response.data;
  },

  // Get all weekly summaries, optionally filtered by source type
  getWeeklySummaries: async (sourceType = null) => {
    const params = sourceType ? { source_type: sourceType } : {};
    const response = await axios.get('/api/weekly/summaries', { params });
    return response.data;
  },

  // Get analysis history
  getAnalysisHistory: async () => {
    try {
      // Use a specific configuration to indicate this doesn't need authentication
      const response = await axios.get('/api/history', {
        headers: {
          // Explicitly remove any Authorization header
          'Authorization': ''
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching analysis history:', error);
      return [];
    }
  },

  // Get specific analysis by ID
  getAnalysisById: async (analysisId) => {
    try {
      const response = await axios.get(`/api/history/${analysisId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching analysis with ID ${analysisId}:`, error);
      return null;
    }
  },

  // Delete analysis by ID
  deleteAnalysis: async (analysisId) => {
    try {
      await axios.delete(`/api/history/${analysisId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting analysis with ID ${analysisId}:`, error);
      throw error;
    }
  },

  async getAnalytics() {
    try {
      const response = await axios.get('/api/analytics');
      return response.data;
    } catch (error) {
      console.error('Error fetching analytics:', error);
      throw error;
    }
  },

  async getPriorityInsights(sourceType, timeRange = 'week') {
    try {
      const response = await axios.get('/api/weekly/priorities', {
        params: {
          source_type: sourceType,
          time_range: timeRange
        },
        headers: {
          // Explicitly remove any Authorization header
          'Authorization': ''
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching insights:', error);
      throw error;
    }
  },

  async getReviews(filters = {}) {
    try {
      const response = await axios.get('/api/reviews', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching reviews:', error);
      throw error;
    }
  },

  async scrapeReviews(source) {
    try {
      const response = await axios.post('/api/scrape', { source });
      return response.data;
    } catch (error) {
      console.error('Error scraping reviews:', error);
      throw error;
    }
  },

  async downloadPDF(filters = {}) {
    try {
      // Use the same endpoint as the downloadPDF method above
      const response = await axios.post('/api/summary/pdf', filters, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `product_review_summary_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      throw error;
    }
  }
};

export default api;
