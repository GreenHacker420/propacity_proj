import React from 'react';
import { motion } from 'framer-motion';

/**
 * Component for displaying analyzed reviews in a table
 */
const ReviewsTable = ({ reviews }) => {
  if (!reviews || reviews.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No reviews to display
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white rounded-lg overflow-hidden shadow">
        <thead className="bg-gray-100">
          <tr>
            {reviews[0].source === 'github' && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue</th>
            )}
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Text</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sentiment</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keywords</th>
            {reviews.some(r => r.rating) && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rating</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {reviews.map((review, index) => (
            <motion.tr
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              {review.source === 'github' && (
                <td className="px-6 py-4 whitespace-normal text-sm font-medium text-primary-600">
                  {review.issue_title}
                </td>
              )}
              <td className="px-6 py-4 whitespace-normal text-sm text-gray-900">{review.text}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  review.sentiment_label === 'POSITIVE'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {review.sentiment_label} ({review.sentiment_score.toFixed(2)})
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  review.category === 'pain_point'
                    ? 'bg-red-100 text-red-800'
                    : review.category === 'feature_request'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-green-100 text-green-800'
                }`}>
                  {review.category.replace('_', ' ')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                {Array.isArray(review.keywords) ? review.keywords.join(', ') : review.keywords}
              </td>
              {reviews.some(r => r.rating) && (
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {review.rating ? review.rating : '-'}
                </td>
              )}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ReviewsTable;
