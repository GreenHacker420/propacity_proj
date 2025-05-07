import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { DocumentTextIcon, ChartPieIcon, ArrowLeftIcon, ClockIcon } from '@heroicons/react/24/outline';
import ConfirmationDialog from './ConfirmationDialog';

/**
 * Header component with navigation buttons
 */
const Header = ({
  hasData,
  activeView,
  setActiveView,
  hasSummary,
  onDownloadPDF,
  onReset,
  onShowHistory,
  loading
}) => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  return (
    <motion.header
      className="flex justify-between items-center mb-8"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center">
        {hasData && (
          <motion.button
            className="mr-4 p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
            onClick={() => setShowConfirmDialog(true)}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="Back to input"
          >
            <ArrowLeftIcon className="w-5 h-5 text-gray-700" />
          </motion.button>
        )}
        <h1 className="text-3xl font-bold text-gray-900">Product Review Analyzer</h1>

        {/* History Button */}
        <motion.button
          className="ml-4 p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
          onClick={onShowHistory}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title="View Analysis History"
        >
          <ClockIcon className="w-5 h-5 text-gray-700" />
        </motion.button>
      </div>

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

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={showConfirmDialog}
        onClose={() => setShowConfirmDialog(false)}
        onConfirm={onReset}
        title="Return to Input"
        message="Are you sure you want to go back? Your current analysis data will be lost."
        confirmText="Yes, go back"
        cancelText="Cancel"
      />
    </motion.header>
  );
};

export default Header;
