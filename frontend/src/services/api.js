import axios from 'axios';
import { getToken } from './authService';

// Always use the direct backend URL to avoid proxy issues
const baseURL = 'http://localhost:8000';

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

// Add request interceptor for authentication
axios.interceptors.request.use(
  config => {
    const token = getToken();
    // console.log('Auth token:', token); // Debug log
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      // console.log('Request headers:', config.headers); // Debug log
    } else {
      // console.warn('No auth token found'); // Debug log
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

  // Get Gemini service status
  getGeminiStatus: async () => {
    try {
      const response = await axios.get('/api/gemini/status');
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

    // Use direct URL to backend to avoid proxy issues
    const response = await axios.post('http://localhost:8000/api/upload', formData, {
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

    const response = await axios.get('/api/scrape', { params });
    return response.data;
  },

  // Perform sentiment analysis on a batch of texts
  analyzeSentiment: async (texts) => {
    const response = await axios.post('/api/sentiment/batch', { texts });
    return response.data;
  },

  // Generate summary from analyzed reviews
  generateSummary: async (reviewsData) => {
    const response = await axios.post('/api/summary', reviewsData);
    return response.data;
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
    // Use direct URL to backend to avoid proxy issues
    await axios.post('http://localhost:8000/api/history', {
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
  getPriorityInsights: async (sourceType = null) => {
    const params = sourceType ? { source_type: sourceType } : {};
    const response = await axios.get('/api/weekly/priorities', { params });
    return response.data;
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
  
    // Get prioritized insights from recent feedback
    getPriorityInsights: async (sourceType = null) => {
      const params = sourceType ? { source_type: sourceType } : {};
      const response = await axios.get('/api/weekly/priorities', { params });
      return response.data;
    },

  // Get analysis history
  getAnalysisHistory: async () => {
    try {
      const response = await axios.get('/api/history');
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
  }
};

export default api;
