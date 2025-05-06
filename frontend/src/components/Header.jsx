import React from 'react';
import { motion } from 'framer-motion';
import { DocumentTextIcon, ChartPieIcon } from '@heroicons/react/24/outline';

/**
 * Header component with navigation buttons
 */
const Header = ({ 
  hasData, 
  activeView, 
  setActiveView, 
  hasSummary, 
  onDownloadPDF, 
  loading 
}) => {
  return (
    <motion.header
      className="flex justify-between items-center mb-8"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h1 className="text-3xl font-bold text-gray-900">Product Review Analyzer</h1>

      {hasData && (
        <motion.div
          className="flex space-x-2"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <button
            className={`btn ${activeView === 'reviews' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveView('reviews')}
          >
            <DocumentTextIcon className="w-5 h-5 inline-block mr-2" />
            Reviews
          </button>
          <button
            className={`btn ${activeView === 'summary' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveView('summary')}
          >
            <ChartPieIcon className="w-5 h-5 inline-block mr-2" />
            Summary
          </button>
          {hasSummary && (
            <button
              className="btn btn-primary"
              onClick={onDownloadPDF}
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Download PDF'}
            </button>
          )}
        </motion.div>
      )}
    </motion.header>
  );
};

export default Header;
