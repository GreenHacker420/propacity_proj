import React, { useState } from 'react';
import { motion } from 'framer-motion';
import DataVisualization from './DataVisualization';
import ReviewsTable from './ReviewsTable';
import WeeklySummaryView from './WeeklySummaryView';

/**
 * Component for displaying the summary of analyzed reviews
 */
const SummaryView = ({ summary, onDownloadPDF }) => {
  const [activeView, setActiveView] = useState('analysis');

  // For backward compatibility, use summary prop but fallback to data if needed
  const data = summary || null;

  if (!data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
        <p className="font-medium">No summary data available. There might have been an error generating the summary.</p>
      </div>
    );
  }

  // Log the data structure to help with debugging
  console.log('Summary data structure:', Object.keys(data));

  // Check for API errors in the summary data
  const hasApiError = data.error && data.error_source === "gemini_api";
  const isQuotaError = hasApiError && data.error && data.error.includes && data.error.includes("quota");

  // Check for rate limit or circuit breaker in the data
  const isRateLimited = data.rate_limited === true || (data.summary && data.summary.includes && data.summary.includes("Rate limit exceeded"));
  const isCircuitOpen = data.circuit_open === true || (data.summary && data.summary.includes && data.summary.includes("circuit breaker"));

  return (
    <div className="space-y-8">
      {/* API Error Message */}
      {(hasApiError || isRateLimited || isCircuitOpen) && (
        <div className={`p-4 rounded-lg mb-4 ${
          isQuotaError || isRateLimited
            ? 'bg-blue-50 border border-blue-200 text-blue-800'
            : isCircuitOpen
              ? 'bg-orange-50 border border-orange-200 text-orange-800'
              : 'bg-yellow-50 border border-yellow-200 text-yellow-800'
        }`}>
          <p className="font-medium">
            {isQuotaError || isRateLimited
              ? 'AI quota exceeded. The summary was generated using basic analysis instead of advanced AI.'
              : isCircuitOpen
                ? 'Circuit breaker active. The system is temporarily using local processing.'
                : 'There was an issue with the AI service. The summary was generated using basic analysis.'}
          </p>
          <p className="text-sm mt-2">
            {isQuotaError || isRateLimited
              ? 'This happens when the daily limit for AI requests is reached. The system automatically switched to a simpler analysis method.'
              : isCircuitOpen
                ? 'After multiple API failures, the system temporarily switched to local processing to ensure reliability.'
                : 'The system automatically switched to a simpler analysis method.'}
          </p>
        </div>
      )}

      {/* View Selector Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          className={`px-4 py-2 font-medium ${
            activeView === 'analysis'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveView('analysis')}
        >
          Analysis
        </button>
        <button
          className={`px-4 py-2 font-medium ${
            activeView === 'weekly'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveView('weekly')}
        >
          Weekly PM Summary
        </button>
      </div>

      {activeView === 'analysis' && (
        <>
          {/* Data Visualization Section */}
          <DataVisualization data={data} />

          {/* Reviews Table Section */}
          <div className="bg-white rounded-lg shadow-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Detailed Reviews</h3>
              <button
                onClick={onDownloadPDF}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                Download PDF Report
              </button>
            </div>
            {data.reviews && data.reviews.length > 0 ? (
              <ReviewsTable reviews={data.reviews} />
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4">
                <p className="font-medium">No review data available. There might have been an error processing the reviews.</p>
              </div>
            )}
          </div>
        </>
      )}

      {activeView === 'weekly' && (
        <WeeklySummaryView sourceType={data.source_type || 'unknown'} />
      )}
    </div>
  );
};

export default SummaryView;
