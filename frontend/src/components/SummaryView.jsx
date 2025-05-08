import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import DataVisualization from './DataVisualization';
import ReviewsTable from './ReviewsTable';
import WeeklySummaryView from './WeeklySummaryView';

/**
 * Component for displaying the summary of analyzed reviews
 */
const SummaryView = ({ summary, onDownloadPDF }) => {
  const [activeView, setActiveView] = useState('analysis');
  const [isLoading, setIsLoading] = useState(false);

  // For backward compatibility, use summary prop but fallback to data if needed
  const data = summary || null;

  // Effect to track when data changes
  useEffect(() => {
    if (data) {
      console.log('Summary data updated:', Object.keys(data));
      setIsLoading(false);
    }
  }, [data]);

  if (!data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
        <p className="font-medium">No summary data available. There might have been an error generating the summary.</p>
      </div>
    );
  }

  // Check for API errors in the summary data
  const hasApiError = data.error && data.error_source === "gemini_api";
  const isQuotaError = hasApiError && data.error &&
    (typeof data.error === 'string' && data.error.includes("quota"));

  // Check for rate limit or circuit breaker in the data
  const isRateLimited = data.rate_limited === true ||
    (data.summary && typeof data.summary === 'string' && data.summary.includes("Rate limit exceeded"));
  const isCircuitOpen = data.circuit_open === true ||
    (data.summary && typeof data.summary === 'string' && data.summary.includes("circuit breaker"));

  return (
    <div className="space-y-8">
      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        <button
          className={`px-6 py-3 rounded-lg transition-all duration-200 font-medium ${
            activeView === 'analysis'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          }`}
          onClick={() => setActiveView('analysis')}
        >
          Analysis
        </button>
        <button
          className={`px-6 py-3 rounded-lg transition-all duration-200 font-medium ${
            activeView === 'weekly'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          }`}
          onClick={() => setActiveView('weekly')}
        >
          Weekly PM Summary
        </button>
      </div>

      {activeView === 'analysis' && (
        <div className="space-y-8">
          {/* Data Visualization Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <DataVisualization data={data} />
          </div>

          {/* Reviews Table Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-semibold text-gray-900">Detailed Reviews</h3>
              <button
                onClick={onDownloadPDF}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download PDF Report</span>
              </button>
            </div>
            {data.reviews && data.reviews.length > 0 ? (
              <ReviewsTable reviews={data.reviews} />
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-6 text-center">
                <p className="font-medium text-lg mb-4">No review data available in this view.</p>
                <p className="text-yellow-700 mb-6">Try switching to the Weekly PM Summary tab to see insights.</p>
                <button
                  onClick={() => setActiveView('weekly')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  View Weekly Summary
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === 'weekly' && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <WeeklySummaryView
            sourceType={data.source_type || 'unknown'}
            key={`weekly-${data.source_type || 'unknown'}`}
          />
        </div>
      )}
    </div>
  );
};

export default SummaryView;
