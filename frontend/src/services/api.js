import axios from 'axios';

// Configure axios base URL to match the backend server port
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.withCredentials = true;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// API status tracking
let apiStatus = {
  error: null,
  lastErrorTime: null,
  quotaExceeded: false,
  retryAfter: null
};

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
  // Upload and analyze a CSV file
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
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

  // Analyze GitHub repository
  analyzeGitHub: async (url) => {
    // This is a placeholder for the actual GitHub analysis API
    // For now, we'll simulate the API call with mock data
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Create mock data for GitHub analysis
    const mockGitHubData = {
      issues: [
        { id: 1, title: "App crashes when uploading large files", body: "When I try to upload files larger than 10MB, the app crashes without any error message.", labels: ["bug", "high-priority"] },
        { id: 2, title: "Add dark mode support", body: "It would be great to have a dark mode option for the UI.", labels: ["enhancement", "ui"] },
        { id: 3, title: "Search functionality not working properly", body: "The search doesn't return results for partial matches.", labels: ["bug"] }
      ],
      discussions: [
        { id: 1, title: "Roadmap for v2.0", body: "Let's discuss the features we want to include in version 2.0" },
        { id: 2, title: "Performance improvements", body: "We should focus on improving load times for the dashboard" }
      ]
    };

    // Create mock analyzed reviews from GitHub data
    const mockAnalyzedReviews = mockGitHubData.issues.map(issue => ({
      text: issue.body,
      sentiment_label: issue.labels.includes("bug") ? "NEGATIVE" : "POSITIVE",
      sentiment_score: issue.labels.includes("bug") ? 0.2 : 0.8,
      category: issue.labels.includes("bug") ? "pain_point" :
               issue.labels.includes("enhancement") ? "feature_request" : "positive_feedback",
      keywords: issue.labels,
      source: "github",
      issue_title: issue.title
    }));

    return {
      repoData: mockGitHubData,
      analyzedReviews: mockAnalyzedReviews
    };
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
  }
};

export default api;
