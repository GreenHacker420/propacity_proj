import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BoltIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';

const APIQuotaDisplay = ({ apiStatus, className = '' }) => {
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (!apiStatus || !apiStatus.error) {
      setIsVisible(false);
      return;
    }

    setIsVisible(true);

    // Extract retry delay from error message
    const retryMatch = apiStatus.error.match(/retry_delay"[\s\S]*?seconds":\s*(\d+)/);
    if (retryMatch && retryMatch[1]) {
      const retrySeconds = parseInt(retryMatch[1]);
      setTimeRemaining(retrySeconds);

      // Update countdown timer
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [apiStatus]);

  if (!isVisible) return null;

  // Extract model information
  const modelMatch = apiStatus.error.match(/model"[\s\S]*?"value":\s*"([^"]+)"/);
  const model = modelMatch ? modelMatch[1] : 'Gemini API';

  // Extract quota limit
  const limitMatch = apiStatus.error.match(/quota_value":\s*(\d+)/);
  const limit = limitMatch ? parseInt(limitMatch[1]) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className={`bg-gradient-to-r from-amber-50 to-amber-100 rounded-lg p-4 shadow-md border border-amber-200 ${className}`}
    >
      <div className="flex items-center space-x-3">
        <div className="flex-shrink-0">
          <div className="bg-amber-100 p-2 rounded-full">
            <BoltIcon className="h-6 w-6 text-amber-600" />
          </div>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-amber-800">API Quota Status</h3>
          <div className="mt-1 text-xs text-amber-700">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-4 w-4 text-amber-500 mr-1" />
              <span>
                {model} quota limit reached ({limit} requests/minute)
              </span>
            </div>
            {timeRemaining > 0 && (
              <div className="flex items-center mt-1">
                <ClockIcon className="h-4 w-4 text-amber-500 mr-1" />
                <span>
                  Quota resets in: <span className="font-medium">{Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}</span>
                </span>
              </div>
            )}
            <div className="mt-2 text-xs">
              <span className="font-medium">Note:</span> The system is automatically falling back to alternative analysis methods.
            </div>
          </div>
        </div>
      </div>
      {timeRemaining > 0 && (
        <div className="mt-2 bg-white rounded-full h-1.5 overflow-hidden">
          <motion.div
            className="bg-amber-500 h-full"
            initial={{ width: '100%' }}
            animate={{ width: '0%' }}
            transition={{ duration: timeRemaining, ease: 'linear' }}
          />
        </div>
      )}
    </motion.div>
  );
};

export default APIQuotaDisplay;
