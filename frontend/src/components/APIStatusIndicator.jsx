import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ExclamationTriangleIcon, InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/solid';

const APIStatusIndicator = ({ 
  apiStatus, 
  onClose, 
  showDetails = false,
  autoHide = true,
  hideAfter = 10000 // 10 seconds
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [showMore, setShowMore] = useState(false);

  useEffect(() => {
    if (autoHide && apiStatus?.error) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose();
      }, hideAfter);
      
      return () => clearTimeout(timer);
    }
  }, [apiStatus, autoHide, hideAfter, onClose]);

  if (!apiStatus || !apiStatus.error || !isVisible) {
    return null;
  }

  // Extract quota information from error message
  const extractQuotaInfo = (errorMessage) => {
    const quotaInfo = {
      model: null,
      limit: null,
      retryDelay: null
    };

    try {
      // Extract model
      const modelMatch = errorMessage.match(/model"[\s\S]*?"value":\s*"([^"]+)"/);
      if (modelMatch && modelMatch[1]) {
        quotaInfo.model = modelMatch[1];
      }

      // Extract quota limit
      const limitMatch = errorMessage.match(/quota_value":\s*(\d+)/);
      if (limitMatch && limitMatch[1]) {
        quotaInfo.limit = parseInt(limitMatch[1]);
      }

      // Extract retry delay
      const retryMatch = errorMessage.match(/retry_delay"[\s\S]*?seconds":\s*(\d+)/);
      if (retryMatch && retryMatch[1]) {
        quotaInfo.retryDelay = parseInt(retryMatch[1]);
      }
    } catch (e) {
      console.error("Error parsing quota info:", e);
    }

    return quotaInfo;
  };

  const quotaInfo = extractQuotaInfo(apiStatus.error);
  const isQuotaError = apiStatus.error.includes("quota");

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`rounded-lg p-4 mb-4 shadow-md ${
          isQuotaError ? 'bg-amber-50 border border-amber-200' : 'bg-red-50 border border-red-200'
        }`}
      >
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {isQuotaError ? (
              <ExclamationTriangleIcon className="h-5 w-5 text-amber-500" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            )}
          </div>
          <div className="ml-3 flex-1">
            <h3 className={`text-sm font-medium ${isQuotaError ? 'text-amber-800' : 'text-red-800'}`}>
              {isQuotaError ? 'API Quota Limit Reached' : 'API Error'}
            </h3>
            <div className={`mt-1 text-sm ${isQuotaError ? 'text-amber-700' : 'text-red-700'}`}>
              {isQuotaError ? (
                <p>
                  The Gemini API quota limit has been reached. The system will automatically fall back to alternative analysis methods.
                  {quotaInfo.retryDelay && (
                    <span className="font-medium"> Quota will reset in approximately {Math.floor(quotaInfo.retryDelay / 60)} minute(s).</span>
                  )}
                </p>
              ) : (
                <p>{apiStatus.error.substring(0, 100)}...</p>
              )}
              
              {showDetails && (
                <button 
                  onClick={() => setShowMore(!showMore)}
                  className={`mt-1 text-xs font-medium underline ${isQuotaError ? 'text-amber-800' : 'text-red-800'}`}
                >
                  {showMore ? 'Show less' : 'Show details'}
                </button>
              )}
              
              {showMore && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-2 text-xs bg-white/50 p-2 rounded border border-gray-200 overflow-auto max-h-32"
                >
                  <pre className="whitespace-pre-wrap">{apiStatus.error}</pre>
                </motion.div>
              )}
              
              {quotaInfo.model && (
                <div className="mt-2 flex items-center">
                  <InformationCircleIcon className="h-4 w-4 text-amber-500 mr-1" />
                  <span className="text-xs">
                    Model: <span className="font-medium">{quotaInfo.model}</span>
                    {quotaInfo.limit && (
                      <span> | Limit: <span className="font-medium">{quotaInfo.limit} requests/minute</span></span>
                    )}
                  </span>
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              if (onClose) onClose();
            }}
            className="flex-shrink-0 ml-2"
          >
            <XMarkIcon className={`h-4 w-4 ${isQuotaError ? 'text-amber-500' : 'text-red-500'}`} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default APIStatusIndicator;
