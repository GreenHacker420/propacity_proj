import React from 'react';
import { motion } from 'framer-motion';

/**
 * Component for displaying the summary of analyzed reviews
 */
const SummaryView = ({ summary }) => {
  if (!summary) {
    return (
      <div className="text-center py-8 text-gray-500">
        No summary available
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Feedback Analysis Summary</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pain Points */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Pain Points</h3>
          <div className="space-y-4">
            {summary.pain_points.length > 0 ? (
              summary.pain_points.map((item, index) => (
                <motion.div
                  key={index}
                  className="p-4 bg-red-50 rounded-md"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <p className="text-sm text-gray-700">{item.text}</p>
                  <div className="mt-2 flex justify-between text-xs text-gray-500">
                    <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                    <span>Keywords: {item.keywords.join(', ')}</span>
                  </div>
                </motion.div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">No pain points identified</p>
            )}
          </div>
        </motion.div>

        {/* Feature Requests */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Feature Requests</h3>
          <div className="space-y-4">
            {summary.feature_requests.length > 0 ? (
              summary.feature_requests.map((item, index) => (
                <motion.div
                  key={index}
                  className="p-4 bg-blue-50 rounded-md"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <p className="text-sm text-gray-700">{item.text}</p>
                  <div className="mt-2 flex justify-between text-xs text-gray-500">
                    <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                    <span>Keywords: {item.keywords.join(', ')}</span>
                  </div>
                </motion.div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">No feature requests identified</p>
            )}
          </div>
        </motion.div>

        {/* Positive Feedback */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Positive Highlights</h3>
          <div className="space-y-4">
            {summary.positive_feedback.length > 0 ? (
              summary.positive_feedback.map((item, index) => (
                <motion.div
                  key={index}
                  className="p-4 bg-green-50 rounded-md"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <p className="text-sm text-gray-700">{item.text}</p>
                  <div className="mt-2 flex justify-between text-xs text-gray-500">
                    <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                    <span>Keywords: {item.keywords.join(', ')}</span>
                  </div>
                </motion.div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">No positive feedback identified</p>
            )}
          </div>
        </motion.div>
      </div>

      {/* Suggested Priorities */}
      <motion.div
        className="mt-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.3 }}
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Suggested PM Priorities</h3>
        <div className="card">
          <ul className="space-y-3">
            {summary.suggested_priorities.map((priority, index) => (
              <motion.li
                key={index}
                className="flex items-start"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
              >
                <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {index + 1}
                </span>
                <span className="ml-3 text-gray-700">{priority}</span>
              </motion.li>
            ))}
          </ul>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SummaryView;
