import React, { useState } from 'react';
import { motion } from 'framer-motion';
import DataVisualization from './DataVisualization';
import ReviewsTable from './ReviewsTable';
import WeeklySummaryView from './WeeklySummaryView';

/**
 * Component for displaying the summary of analyzed reviews
 */
const SummaryView = ({ data, onDownloadPDF }) => {
  const [activeView, setActiveView] = useState('analysis');

  if (!data) return null;

  return (
    <div className="space-y-8">
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
            <ReviewsTable reviews={data.reviews} />
          </div>
        </>
      )}

      {activeView === 'weekly' && (
        <WeeklySummaryView sourceType={data.source_type} />
      )}
    </div>
  );
};

export default SummaryView;
