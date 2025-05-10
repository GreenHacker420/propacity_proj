import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClockIcon,
  DocumentTextIcon,
  ChartPieIcon,
  TrashIcon,
  EyeIcon,
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import api from '../services/api';
import LoadingIndicator from './LoadingIndicator';
import ConfirmationDialog from './ConfirmationDialog';
import SummaryView from './SummaryView';

/**
 * Component for displaying analysis history
 */
const HistoryView = ({
  onSelectAnalysis,
  onClose,
  historyData = [],
  isLoading = false,
  onRefresh
}) => {
  const [history, setHistory] = useState(historyData);
  const [loading, setLoading] = useState(isLoading);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [showSummary, setShowSummary] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);

  // Update history when props change
  useEffect(() => {
    setHistory(historyData);
    setLoading(isLoading);
  }, [historyData, isLoading]);

  // Handle refresh button click
  const handleRefresh = async () => {
    if (onRefresh) {
      setRefreshing(true);
      try {
        await onRefresh();
      } catch (err) {
        console.error('Error refreshing history:', err);
        setError('Failed to refresh history. Please try again later.');
      } finally {
        setRefreshing(false);
      }
    } else {
      // Fallback to local refresh if onRefresh not provided
      try {
        setRefreshing(true);
        const data = await api.getAnalysisHistory();
        setHistory(data);
        setError(null);
      } catch (err) {
        console.error('Error refreshing history:', err);
        setError('Failed to refresh history. Please try again later.');
      } finally {
        setRefreshing(false);
      }
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Handle analysis selection
  const handleSelectAnalysis = (analysis) => {
    onSelectAnalysis(analysis);
  };

  // Handle delete confirmation
  const handleDeleteClick = (id, e) => {
    e.stopPropagation(); // Prevent triggering the row click
    setSelectedItemId(id);
    setShowDeleteConfirm(true);
  };

  // Handle actual deletion
  const handleConfirmDelete = async () => {
    try {
      // Call API to delete the analysis
      await api.deleteAnalysis(selectedItemId);

      // Update local state to remove the deleted item without refreshing the entire history
      setHistory(history.filter(item => item._id !== selectedItemId));

      setShowDeleteConfirm(false);
      setSelectedItemId(null);
    } catch (err) {
      console.error('Error deleting analysis:', err);
      setError('Failed to delete analysis. Please try again later.');
    }
  };

  // Handle viewing summary
  const handleViewSummary = (item, e) => {
    e.stopPropagation(); // Prevent triggering the row click
    setSelectedSummary(item);
    setShowSummary(true);
  };

  // Close summary view
  const handleCloseSummary = () => {
    setShowSummary(false);
    setSelectedSummary(null);
  };

  // Get category counts for a history item
  const getCategoryCounts = (item) => {
    return {
      painPoints: item.pain_point_count || 0,
      featureRequests: item.feature_request_count || 0,
      positiveFeedback: item.positive_feedback_count || 0
    };
  };

  // Get sentiment color based on score
  const getSentimentColor = (score) => {
    if (score >= 0.6) return 'text-green-600';
    if (score <= 0.4) return 'text-red-600';
    return 'text-yellow-600';
  };

  return (
    <motion.div
      className="bg-white rounded-lg shadow-lg p-6 w-full max-w-6xl max-h-[85vh] overflow-hidden flex flex-col"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <ClockIcon className="w-6 h-6 mr-2 text-blue-600" />
          Analysis History
        </h2>
        <div className="flex space-x-2">
          <motion.button
            className="btn btn-primary flex items-center"
            onClick={handleRefresh}
            disabled={refreshing || loading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <ArrowPathIcon className={`w-5 h-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </motion.button>
          <button
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex justify-center items-center py-12">
          <LoadingIndicator size={40} />
          <p className="ml-4 text-gray-600">Loading history...</p>
        </div>
      ) : refreshing ? (
        <div className="flex-1 flex justify-center items-center py-12">
          <LoadingIndicator size={40} />
          <p className="ml-4 text-gray-600">Refreshing history...</p>
        </div>
      ) : error ? (
        <div className="flex-1 bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-4">
          <p className="font-medium">{error}</p>
        </div>
      ) : history.length === 0 ? (
        <div className="flex-1 bg-gray-50 border border-gray-200 text-gray-800 rounded-lg p-8 mt-4 text-center">
          <p className="font-medium text-lg">No analysis history found</p>
          <p className="text-gray-600 mt-2">Complete an analysis to see it here</p>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="overflow-y-auto overflow-x-auto flex-1">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Records
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sentiment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categories
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <AnimatePresence>
                {history.map((item) => {
                  const categoryCounts = getCategoryCounts(item);
                  return (
                    <motion.tr
                      key={item._id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => handleSelectAnalysis(item)}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm font-medium text-gray-900">
                            {item.source_type}
                          </div>
                          <div className="text-sm text-gray-500 ml-1">
                            ({item.source_name})
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(item.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.record_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-medium ${getSentimentColor(item.avg_sentiment_score)}`}>
                          {(item.avg_sentiment_score * 100).toFixed(1)}%
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex space-x-2">
                          <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                            {categoryCounts.painPoints} Pain Points
                          </span>
                          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                            {categoryCounts.featureRequests} Requests
                          </span>
                          <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            {categoryCounts.positiveFeedback} Positive
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={(e) => handleViewSummary(item, e)}
                            className="text-blue-600 hover:text-blue-900"
                            title="View Summary"
                          >
                            <EyeIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={(e) => handleDeleteClick(item._id, e)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete Analysis"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </AnimatePresence>
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* Confirmation Dialog for Delete */}
      <ConfirmationDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Analysis"
        message="Are you sure you want to delete this analysis? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
      />

      {/* Summary Modal */}
      <AnimatePresence>
        {showSummary && selectedSummary && (
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 flex flex-col h-full">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Summary: {selectedSummary.source_type} ({selectedSummary.source_name})
                  </h2>
                  <button
                    onClick={handleCloseSummary}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                <div className="overflow-y-auto flex-1">
                  <SummaryView summary={selectedSummary.summary} />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default HistoryView;
