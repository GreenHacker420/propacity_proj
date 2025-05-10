import React, { useState } from 'react';

/**
 * Debug component to display raw summary data
 */
const DebugSummary = ({ summary }) => {
  const [expanded, setExpanded] = useState(false);

  if (!summary) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
        <p className="font-medium">No summary data available for debugging.</p>
      </div>
    );
  }

  // Format the summary data for display
  const formattedSummary = JSON.stringify(summary, null, 2);

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-medium text-gray-800">Debug: Summary Data</h3>
        <button
          onClick={() => setExpanded(!expanded)}
          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-md text-sm font-medium"
        >
          {expanded ? 'Collapse' : 'Expand'}
        </button>
      </div>
      
      {expanded && (
        <div className="mt-4">
          <div className="bg-gray-800 text-gray-100 p-4 rounded-md overflow-x-auto">
            <pre className="text-xs">{formattedSummary}</pre>
          </div>
          
          <div className="mt-4 space-y-4">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Summary Keys:</h4>
              <ul className="list-disc list-inside text-sm text-gray-600">
                {Object.keys(summary).map(key => (
                  <li key={key}>{key}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Required Keys Check:</h4>
              <ul className="list-disc list-inside text-sm">
                <li className={summary.pain_points ? 'text-green-600' : 'text-red-600'}>
                  pain_points: {summary.pain_points ? 'Present' : 'Missing'}
                </li>
                <li className={summary.feature_requests ? 'text-green-600' : 'text-red-600'}>
                  feature_requests: {summary.feature_requests ? 'Present' : 'Missing'}
                </li>
                <li className={summary.positive_feedback ? 'text-green-600' : 'text-red-600'}>
                  positive_feedback: {summary.positive_feedback ? 'Present' : 'Missing'}
                </li>
                <li className={summary.suggested_priorities ? 'text-green-600' : 'text-red-600'}>
                  suggested_priorities: {summary.suggested_priorities ? 'Present' : 'Missing'}
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugSummary;
