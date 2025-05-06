import React from 'react';
import { motion } from 'framer-motion';
import DataVisualization from './DataVisualization';
import ReviewsTable from './ReviewsTable';

/**
 * Component for displaying the summary of analyzed reviews
 */
const SummaryView = ({ data, onDownloadPDF }) => {
  if (!data) return null;

  return (
    <div className="space-y-8">
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
    </div>
  );
};

export default SummaryView;
